#!/usr/bin/env python3
"""
BaridOS Panel — Settings & monitoring app
Shows: CPU/GPU temperature, fan RPM/speed, FPS, profile control,
frame limiter, manual fan override, one-click installs (Blender,
GIMP, PrismLauncher Minecraft), AI assistant launcher.
"""
import json
import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

STATE = "/run/barid/thermo.json"
CONF = "/etc/barid/thermo.conf"
MANGOHUD_LOG = os.path.expanduser("~/.config/MangoHud/barid_fps.log")


def load_conf():
    try:
        with open(CONF) as f:
            return json.load(f)
    except Exception:
        return {}


def save_conf(patch):
    conf = load_conf()
    conf.update(patch)
    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    with open(CONF, "w") as f:
        json.dump(conf, f, indent=2)


def sh(cmd):
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Panel(tk.Tk):
    BG = "#101418"
    CARD = "#1a2129"
    FG = "#e8eef4"
    ACCENT = "#38bdf8"
    HOT = "#f87171"
    OK = "#4ade80"

    def __init__(self):
        super().__init__()
        self.title("BaridOS — لوحة التحكم")
        self.configure(bg=self.BG)
        self.geometry("460x640")
        self.resizable(False, False)
        self._build()
        self._tick()

    def _card(self, parent):
        f = tk.Frame(parent, bg=self.CARD, padx=14, pady=10)
        f.pack(fill="x", padx=12, pady=6)
        return f

    def _label(self, parent, text, size=11, color=None, bold=False):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color or self.FG,
                        font=("Segoe UI", size, "bold" if bold else "normal"),
                        anchor="w")

    def _build(self):
        # Header
        head = tk.Frame(self, bg=self.BG)
        head.pack(fill="x", padx=12, pady=(12, 0))
        self._label(head, "⛄ BaridOS", 18, self.ACCENT, True).pack(side="left")
        self._label(head, "لوحة التحكم والتبريد", 10, "#8aa0b4").pack(side="left", padx=10, pady=6)

        # Stats card
        c = self._card(self)
        self._label(c, "درجات الحرارة والمراوح", 11, self.ACCENT, True).pack(anchor="w")
        self.cpu_lbl = self._label(c, "المعالج (CPU): —", 12); self.cpu_lbl.pack(anchor="w", pady=2)
        self.gpu_lbl = self._label(c, "كارت الشاشة (GPU): —", 12); self.gpu_lbl.pack(anchor="w", pady=2)
        self.fan_lbl = self._label(c, "المراوح: —", 12); self.fan_lbl.pack(anchor="w", pady=2)
        self.fps_lbl = self._label(c, "الفريمات (FPS): —", 12); self.fps_lbl.pack(anchor="w", pady=2)

        # Profile card
        c = self._card(self)
        self._label(c, "وضع التبريد", 11, self.ACCENT, True).pack(anchor="w")
        row = tk.Frame(c, bg=self.CARD); row.pack(anchor="w", pady=4)
        self.profile = tk.StringVar(value=load_conf().get("profile", "balanced"))
        for name, ar in [("silent", "هادئ"), ("balanced", "متوازن"), ("performance", "أداء")]:
            ttk.Radiobutton(row, text=ar, value=name, variable=self.profile,
                            command=self._apply_profile).pack(side="left", padx=4)

        # Frame limiter
        c = self._card(self)
        self._label(c, "تحديد الفريمات (FPS Limiter)", 11, self.ACCENT, True).pack(anchor="w")
        row = tk.Frame(c, bg=self.CARD); row.pack(anchor="w", fill="x", pady=4)
        self.fps_var = tk.IntVar(value=int(load_conf().get("frame_limit_on_heat", 60)))
        tk.Scale(row, from_=0, to=240, orient="horizontal", variable=self.fps_var,
                 bg=self.CARD, fg=self.FG, troughcolor="#0b0f13", highlightthickness=0,
                 command=lambda v: save_conf({"frame_limit_on_heat": int(float(v))})).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="تطبيق", command=self._apply_fps, bg=self.ACCENT, fg="#06202e",
                  relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=6)

        # Manual fan
        c = self._card(self)
        self._label(c, "تحكم يدوي في المراوح", 11, self.ACCENT, True).pack(anchor="w")
        row = tk.Frame(c, bg=self.CARD); row.pack(anchor="w", fill="x", pady=4)
        self.fan_var = tk.IntVar(value=50)
        tk.Scale(row, from_=0, to=100, orient="horizontal", variable=self.fan_var,
                 bg=self.CARD, fg=self.FG, troughcolor="#0b0f13", highlightthickness=0).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="تعيين %", command=self._set_fan, bg=self.ACCENT, fg="#06202e",
                  relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=6)

        # Tools card
        c = self._card(self)
        self._label(c, "الأدوات والتطبيقات", 11, self.ACCENT, True).pack(anchor="w")
        row = tk.Frame(c, bg=self.CARD); row.pack(anchor="w", pady=4)
        for txt, cmd in [
            ("ماين كرافت", self._minecraft),
            ("بلندر (3D)", lambda: self._flatpak_install("org.blender.Blender", "Blender")),
            ("جيمب (صور)", lambda: self._flatpak_install("org.gimp.GIMP", "GIMP")),
            ("مساعدك AI", self._ai),
        ]:
            tk.Button(row, text=txt, command=cmd, bg="#243040", fg=self.FG,
                      relief="flat", padx=8, pady=4, font=("Segoe UI", 9)).pack(side="left", padx=3)

        # Updates card
        c = self._card(self)
        self._label(c, "التحديثات", 11, self.ACCENT, True).pack(anchor="w")
        row = tk.Frame(c, bg=self.CARD); row.pack(anchor="w", pady=4)
        self.ver_lbl = self._label(row, f"الإصدار: {self._version()}", 10, "#8aa0b4")
        self.ver_lbl.pack(side="left")
        tk.Button(row, text="فحص التحديثات", command=self._check_updates,
                  bg=self.ACCENT, fg="#06202e", relief="flat",
                  font=("Segoe UI", 9, "bold")).pack(side="right")

        self.status = self._label(self, "", 9, "#8aa0b4")
        self.status.pack(pady=4)

    def _version(self):
        try:
            return open("/opt/barid/VERSION").read().strip()
        except Exception:
            return "؟"

    def _apply_profile(self):
        save_conf({"profile": self.profile.get()})
        self.status.config(text=f"تم ضبط وضع التبريد: {self.profile.get()}")

    def _apply_fps(self):
        subprocess.run(["python3", "/opt/barid/barid-update/fps_limit.py",
                        str(self.fps_var.get())], capture_output=True)
        self.status.config(text=f"تم تحديد الفريمات بـ {self.fps_var.get()} FPS")

    def _set_fan(self):
        subprocess.Popen(["nbfc", "set", "-s", str(self.fan_var.get())],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        save_conf({"profile": "custom", "custom_curve": [[0, self.fan_var.get()], [120, self.fan_var.get()]]})
        self.status.config(text=f"المراوح يدوياً على {self.fan_var.get()}%")

    def _minecraft(self):
        threading.Thread(target=self._mc_thread, daemon=True).start()

    def _mc_thread(self):
        self.status.config(text="جاري فتح ماين كرافت...")
        if not subprocess.run(["flatpak", "info", "org.prismlauncher.PrismLauncher"],
                              capture_output=True).returncode == 0:
            self.status.config(text="جاري تثبيت PrismLauncher (أول مرة فقط)...")
            subprocess.run(["flatpak", "install", "-y", "flathub", "org.prismlauncher.PrismLauncher"],
                           capture_output=True)
        sh(["flatpak", "run", "org.prismlauncher.PrismLauncher"])
        self.status.config(text="")

    def _flatpak_install(self, app_id, name):
        threading.Thread(target=lambda: (
            self.status.config(text=f"جاري تثبيت {name}..."),
            subprocess.run(["flatpak", "install", "-y", "flathub", app_id], capture_output=True),
            self.status.config(text=f"تم تثبيت {name} ✔")
        ), daemon=True).start()

    def _ai(self):
        sh(["python3", "/opt/barid/barid-ai/yesaedak_gui.py"])

    def _check_updates(self):
        threading.Thread(target=lambda: (
            self.status.config(text="جاري فحص التحديثات من Supabase..."),
            subprocess.run(["python3", "/opt/barid/barid-update/updater.py", "--check"],
                           capture_output=True),
            self.status.config(text="تم الفحص — شغّل: barid-update لتطبيق التحديثات")
        ), daemon=True).start()

    def _read_fps(self):
        import glob
        try:
            logs = sorted(glob.glob(os.path.expanduser("~/.config/MangoHud/MangoHud*.csv")))
            if not logs or time.time() - os.path.getmtime(logs[-1]) > 30:
                return None  # no recent game log
            lines = open(logs[-1]).read().strip().splitlines()
            return lines[-1].split(",")[-1].strip() if lines else None
        except Exception:
            return None

    def _tick(self):
        try:
            state = json.load(open(STATE))
            cpu = state.get("cpu_temp"); gpu = state.get("gpu_temp")
            def fmt(v): return f"{v:.0f}°C" if isinstance(v, (int, float)) else "—"
            for lbl, v in ((self.cpu_lbl, cpu), (self.gpu_lbl, gpu)):
                lbl.config(text=lbl["text"].split(":")[0] + ": " + fmt(v),
                           fg=self.HOT if isinstance(v, (int, float)) and v >= 80 else self.OK)
            rpm = state.get("fan_rpm"); spd = state.get("fan_speed")
            self.fan_lbl.config(text=f"المراوح: {f'{rpm} RPM' if rpm else '—'}"
                                     + (f"  ({spd}%)" if spd is not None else ""))
            fps = self._read_fps()
            self.fps_lbl.config(text=f"الفريمات (FPS): {fps}" if fps else "الفريمات (FPS): شغّل لعبة أولاً")
        except Exception:
            pass
        self.after(1000, self._tick)


if __name__ == "__main__":
    Panel().mainloop()
