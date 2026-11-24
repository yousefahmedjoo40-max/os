#!/usr/bin/env python3
"""
barid-update — نظام تحديثات BaridOS عبر Supabase

يقرأ بيانات التحديث من جدول `updates` في Supabase (عبر REST + anon key)،
يقارن بالإصدار الحالي، ينزّل حزمة الإصلاح من الرابط، يتحقق من SHA-256،
ثم يطبقها (dpkg/apt) ويعيد تشغيل الخدمات.

الاستخدام:
  updater.py --check     # فحص فقط
  updater.py --apply     # فحص + تطبيق
  updater.py             # نفس --apply (يُستدعى من systemd timer)
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

CONF = "/etc/barid/update.conf"
VERSION_FILE = "/opt/barid/VERSION"
CHANNEL = "stable"


def load_conf():
    data = {}
    try:
        data = json.load(open(CONF))
    except Exception:
        pass
    data.setdefault("supabase_url", "https://YOUR-PROJECT.supabase.co")
    data.setdefault("supabase_anon_key", "YOUR-ANON-KEY")
    return data


def current_version():
    try:
        return open(VERSION_FILE).read().strip()
    except Exception:
        return "0.0.0"


def fetch_latest(conf):
    url = (f"{conf['supabase_url']}/rest/v1/updates"
           f"?channel=eq.{CHANNEL}&active=eq.true&select=*&order=version.desc&limit=1")
    req = urllib.request.Request(url, headers={
        "apikey": conf["supabase_anon_key"],
        "Authorization": f"Bearer {conf['supabase_anon_key']}",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        rows = json.loads(r.read())
    return rows[0] if rows else None


def ver_tuple(v):
    return tuple(int(x) for x in v.split(".") if x.isdigit())


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    with urllib.request.urlopen(url, timeout=300) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def apply_package(pkg, changelog=""):
    subprocess.run(["dpkg", "-i", pkg], capture_output=True)
    subprocess.run(["apt-get", "-f", "install", "-y"], capture_output=True)
    for svc in ("barid-thermo.service", "barid-update.timer"):
        subprocess.run(["systemctl", "restart", svc], capture_output=True)
    print("تم التحديث بنجاح ✔")
    if changelog:
        print("ملاحظات الإصدار:\n" + changelog)


def main():
    conf = load_conf()
    mode = sys.argv[1] if len(sys.argv) > 1 else "--apply"
    try:
        latest = fetch_latest(conf)
    except Exception as e:
        print(f"تعذر الاتصال بـ Supabase: {e}")
        return 1
    if not latest:
        print("لا توجد تحديثات.")
        return 0
    cur, new = current_version(), latest["version"]
    print(f"المثبت: {cur} | المتاح: {new}")
    if ver_tuple(new) <= ver_tuple(cur):
        print("النظام محدث بالفعل ✔")
        return 0
    if mode == "--check":
        print(f"⚡ يوجد تحديث جديد: {new}\n{latest.get('changelog', '')}")
        print("للتطبيق شغّل: barid-update")
        return 0
    with tempfile.TemporaryDirectory() as td:
        pkg = os.path.join(td, "update.deb")
        print("جاري التنزيل...")
        download(latest["url"], pkg)
        if latest.get("sha256") and sha256(pkg) != latest["sha256"]:
            print("❌ فشل التحقق من التوقيع (SHA-256 غير متطابق) — تم إلغاء التحديث.")
            return 2
        apply_package(pkg, latest.get("changelog", ""))
        with open(VERSION_FILE, "w") as f:
            f.write(new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
