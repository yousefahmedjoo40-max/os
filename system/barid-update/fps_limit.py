#!/usr/bin/env python3
"""fps_limit.py — تغيير حد الفريمات العام (MangoHud) من أي مكان."""
import sys

conf = "/etc/MangoHud/MangoHud.conf"
fps = sys.argv[1] if len(sys.argv) > 1 else "0"
try:
    lines = open(conf).read().splitlines()
except FileNotFoundError:
    lines = []
lines = [l for l in lines if not l.startswith("fps_limit")]
lines.insert(0, f"fps_limit={fps}")
with open(conf, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"fps_limit={fps}")
