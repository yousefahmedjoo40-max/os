#!/usr/bin/env python3
"""
يساعدك (Yesaedak) — مساعد BaridOS الذكي
CLI + مكتبة، يعمل بموديل Gemini 3.5 Flash-Lite (Free Tier).

مفتاح الـ API يُقرأ من (بالترتيب):
  1. ~/.config/barid/ai.conf
  2. /etc/barid/ai.conf
أو من متغير البيئة BARID_AI_KEY

الاستخدام:
  yesaedak "سؤالك هنا"
  yesaedak --set-key YOUR_API_KEY
  yesaedak --model gemini-3.5-flash-lite
  echo "نص" | yesaedak            # من stdin
"""
import json
import os
import sys
import urllib.request
import urllib.error

MODEL = "gemini-3.5-flash-lite"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
KEY_PATHS = [os.path.expanduser("~/.config/barid/ai.conf"), "/etc/barid/ai.conf"]

SYSTEM_PROMPT = """أنت "يساعدك"، المساعد الذكي الرسمي لنظام BaridOS — نظام تشغيل عربي خفيف
مهتم بتبريد الأجهزة وتقييد الفريمات وتشغيل الألعاب.
أجب بالعربية البسيطة (مصرية عند الحاجة)، بإجابات قصيرة وعملية وواضحة.
ساعد المستخدم في: إعدادات النظام، التبريد والمراوح، الألعاب وماين كرافت،
البرمجة، وأي سؤال عام. لو سألك عن حرارة جهازه، اطلب منه يفتح "لوحة BaridOS"."""


def load_key():
    if os.environ.get("BARID_AI_KEY"):
        return os.environ["BARID_AI_KEY"].strip()
    for p in KEY_PATHS:
        try:
            data = json.load(open(p))
            if data.get("api_key"):
                return data["api_key"].strip()
        except Exception:
            continue
    return None


def save_key(key, model=None):
    p = os.path.expanduser("~/.config/barid/ai.conf")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = {}
    try:
        data = json.load(open(p))
    except Exception:
        pass
    data["api_key"] = key
    if model:
        data["model"] = model
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(p, 0o600)


def load_model():
    for p in KEY_PATHS:
        try:
            m = json.load(open(p)).get("model")
            if m:
                return m
        except Exception:
            continue
    return MODEL


def ask(prompt, history=None):
    """Send prompt to Gemini 3.5 Flash-Lite and return reply text."""
    key = load_key()
    if not key:
        return ("❌ مفيش مفتاح API. شغّل: yesaedak --set-key YOUR_KEY "
                "(الملف: ~/.config/barid/ai.conf)")
    model = load_model()
    contents = [{"role": "user", "parts": [{"text": prompt}]}]
    if history:
        contents = history + contents
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }).encode()
    req = urllib.request.Request(
        API_URL.format(model=model),
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return (f"❌ الموديل '{model}' غير متاح للمفتاح ده. جرّب: yesaedak --model gemini-3.5-flash-lite")
        if e.code == 429:
            return "⏳ تجاوزت حد الاستخدام المجاني — استنى شوية وحاول تاني."
        return f"❌ خطأ من الخادم: HTTP {e.code}"
    except Exception as e:
        return f"❌ خطأ في الاتصال: {e}"


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "--set-key":
        save_key(args[1])
        print("✔ تم حفظ مفتاح API في ~/.config/barid/ai.conf")
        return
    if args[0] == "--model":
        save_key(load_key() or "", model=args[1])
        print(f"✔ تم ضبط الموديل: {args[1]}")
        return
    prompt = " ".join(args)
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read().strip()
        if stdin_text:
            prompt = stdin_text + "\n\n" + prompt
    print(ask(prompt))


if __name__ == "__main__":
    main()
