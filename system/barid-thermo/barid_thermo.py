#!/usr/bin/env python3
"""
barid-thermo — BaridOS thermal daemon
Reads CPU/GPU temperatures, applies fan profiles, and logs stats
that the BaridOS panel displays. Designed for NVIDIA laptops.

Profiles: silent / balanced / performance / custom
"""
import json
import os
import shutil
import subprocess
import time

CONF_PATH = "/etc/barid/thermo.conf"
STATE_DIR = "/run/barid"
LOG_FILE = os.path.join(STATE_DIR, "thermo.json")

# Fan curve: list of (temp_celsius, fan_speed_percent)
CURVES = {
    "silent":      [(0, 0), (45, 25), (60, 45), (75, 65), (85, 80), (95, 100)],
    "balanced":    [(0, 20), (40, 30), (55, 50), (70, 70), (85, 90), (95, 100)],
    "performance": [(0, 35), (40, 45), (55, 65), (70, 85), (85, 100)],
}

DEFAULTS = {
    "profile": "balanced",
    "poll_seconds": 2,
    "max_temp_action": "notify",   # notify | throttle
    "frame_limit_on_heat": 60,     # FPS cap applied via MangoHud when hot (0 = off)
    "heat_threshold": 80,          # celsius to trigger frame limiting
}


def load_conf():
    conf = dict(DEFAULTS)
    try:
        with open(CONF_PATH) as f:
            conf.update(json.load(f))
    except Exception:
        pass
    return conf


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""


def nvidia_available():
    return shutil.which("nvidia-smi") is not None


def read_gpu_temp():
    if nvidia_available():
        out = sh(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"])
        try:
            return float(out.strip().splitlines()[0])
        except Exception:
            pass
    # Fallback: amdgpu/any hwmon sensor
    for p in ("/sys/class/hwmon/hwmon*/temp1_input", "/sys/class/thermal/thermal_zone*/temp"):
        import glob
        for f in glob.glob(p):
            try:
                v = int(open(f).read().strip())
                return v / 1000.0 if v > 1000 else float(v)
            except Exception:
                continue
    return None


def read_cpu_temp():
    import glob
    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp") + glob.glob("/sys/class/hwmon/hwmon*/temp1_input"):
        try:
            v = int(open(f).read().strip())
            v = v / 1000.0 if v > 1000 else float(v)
            if 20 < v < 130:
                return v
        except Exception:
            continue
    return None


def read_fan_rpm():
    import glob
    rpms = []
    for f in glob.glob("/sys/class/hwmon/hwmon*/fan1_input"):
        try:
            rpms.append(int(open(f).read().strip()))
        except Exception:
            pass
    return rpms[0] if rpms else None


def curve_speed(curve, temp):
    """Interpolate fan speed on the curve."""
    if temp is None:
        return None
    prev_t, prev_s = curve[0]
    for t, s in curve[1:]:
        if temp <= t:
            if t == prev_t:
                return s
            ratio = (temp - prev_t) / (t - prev_t)
            return int(prev_s + ratio * (s - prev_s))
        prev_t, prev_s = t, s
    return curve[-1][1]


def set_fan_speed(percent):
    """Try nbfc (laptop EC) first, then nvidia-smi (desktop GPUs)."""
    ok = False
    if shutil.which("nbfc"):
        r = subprocess.run(["nbfc", "set", "-s", str(percent)],
                           capture_output=True, timeout=5)
        ok = ok or r.returncode == 0
    if nvidia_available():
        out = sh(["nvidia-smi", "--query-gpu=fan.speed", "--format=csv,noheader,nounits"])
        try:
            cur = int(float(out.strip().splitlines()[0]))
            if abs(cur - percent) > 4:  # avoid spamming nvidia-smi
                subprocess.run(["nvidia-smi", "-lfa", str(percent)],
                               capture_output=True, timeout=5)
                ok = True
        except Exception:
            pass
    return ok


def set_frame_limit(fps):
    """Write MangoHud global fps limit (picked up by games at launch)."""
    conf = "/etc/MangoHud/MangoHud.conf"
    try:
        lines = open(conf).read().splitlines()
    except Exception:
        lines = []
    lines = [l for l in lines if not l.startswith("fps_limit")]
    lines.insert(0, f"fps_limit={fps}")
    with open(conf, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    last_speed = -1
    limited = False
    while True:
        conf = load_conf()
        cpu = read_cpu_temp()
        gpu = read_gpu_temp()
        temps = [t for t in (cpu, gpu) if t is not None]
        hottest = max(temps) if temps else None

        custom = conf.get("custom_curve")
        curve = CURVES.get(conf["profile"], CURVES["balanced"])
        if conf["profile"] == "custom" and custom:
            curve = [tuple(p) for p in custom]

        speed = curve_speed(curve, hottest)
        if speed is not None and speed != last_speed:
            if set_fan_speed(speed):
                last_speed = speed

        # Heat protection: cap FPS when running hot
        if conf.get("frame_limit_on_heat", 0) > 0:
            if hottest and hottest >= conf["heat_threshold"] and not limited:
                set_frame_limit(conf["frame_limit_on_heat"])
                limited = True
            elif hottest and hottest < conf["heat_threshold"] - 8 and limited:
                set_frame_limit(0)
                limited = False

        state = {
            "cpu_temp": cpu,
            "gpu_temp": gpu,
            "fan_rpm": read_fan_rpm(),
            "fan_speed": last_speed if last_speed >= 0 else None,
            "profile": conf["profile"],
            "frame_limited": limited,
            "ts": time.time(),
        }
        tmp = LOG_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, LOG_FILE)

        time.sleep(max(1, int(conf.get("poll_seconds", 2))))


if __name__ == "__main__":
    main()
