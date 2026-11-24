# ⛄ BaridOS — نظامك الخاص

توزيعة Linux خفيفة وسريعة مبنية على Debian 13، مصممة للابتوبات بكارت NVIDIA:

| الميزة | التفاصيل |
|---|---|
| ❄️ تبريد ذكي | daemon بيشتغل في الخلفية: thermald + منحنى مراوح تلقائي (هادئ/متوازن/أداء) + تقليل الفريمات تلقائياً لو الجهاز سخن |
| 🎛️ لوحة تحكم | تطبيق يعرض حرارة CPU/GPU وسرعة المراوح والفريمات، ويتحكم فيها يدوياً |
| 🧠 مساعد "يساعدك" | ذكاء اصطناعي كامل بموديل **Gemini 3.5 Flash-Lite** (مجاني — Free Tier) — واجهة محادثة عربية |
| 🔄 تحديثات عبر Supabase | تبعت تحديثات وإصلاحات للمستخدمين من جدول واحد، والنظام بيفحص كل 6 ساعات |
| 🎮 ألعاب | ماين كرافت عبر PrismLauncher (قانوني) + MangoHud للفريمات والحرارة داخل اللعبة |
| 📶 نت بدون إيثرنت | Wi-Fi شغال من أول إقلاع (فيرموير كل الشركات مدموج) |
| 🗜️ مساحة صغيرة | Xfce خفيف + أدوات التصميم (Blender/GIMP) بتتسطب بضغطة واحدة مش داخل الـ ISO |
| 🔗 بناء وتحميل عبر GitHub | GitHub Actions يبني الـ ISO تلقائياً ويرفعه على Releases |

---

## 1️⃣ رفع المشروع على GitHub (ريبو خاص)

```bash
cd baridos
git init
git add .
git commit -m "BaridOS 0.1.0"
git branch -M main
git remote add origin https://github.com/USER/baridos.git   # غيّر USER واسم الريبو
git push -u origin main
```

## 2️⃣ إضافة الأسرار (Settings → Secrets and variables → Actions → New repository secret)

| الاسم | القيمة |
|---|---|
| `BARID_AI_KEY` | مفتاح Gemini API بتاعك — خده من aistudio.google.com → Get API Key |
| `SUPABASE_URL` | الرابط من إعدادات مشروع Supabase (https://xxxx.supabase.co) |
| `SUPABASE_ANON_KEY` | anon/public key من إعدادات المشروع |

> ⚠️ **مهم:** المفتاح اللي بعته في الشات اتكشف علناً — اعمله Revoke من AI Studio واعمل واحد جديد.
> الأسرار دي بتتدفن جوه الـ ISO أثناء البناء و**مش بتتكتب في الكود نهائياً**.

## 3️⃣ بناء الـ ISO والحصول على لينك التحميل

1. من تاب **Actions** → اختار **Build BaridOS ISO** → **Run workflow**
2. استنى 30–90 دقيقة (البناء بياخد وقته)
3. لو عايز **لينك تحميل دائم قابل للنسخ**، اعمل tag:
   ```bash
   git tag v0.1.0 && git push origin v0.1.0
   ```
   وشغّل الـ workflow تاني — الـ ISO هيترفع على Releases تلقائياً.

**لينك التحميل بتاعك هيبقى:**
```
https://github.com/USER/baridos/releases/latest/download/baridos-0.1.0-amd64.iso
```
(غيّر USER ليوزرك — ده اللينك اللي تبعته لأي حد)

أو من صفحة Releases مباشرة: `https://github.com/USER/baridos/releases`

## 4️⃣ حرق الـ ISO على فلاشة

- **Windows:** برنامج Rufus → اختار الـ ISO → Start
- **Linux:** `sudo dd if=baridos-0.1.0-amd64.iso of=/dev/sdX bs=4M status=progress`
- أو Ventoy: انسخ الـ ISO على الفلاشة على طول

شغّل من الفلاشة (Live) أو انصّبه على القرص من أيقونة Install على الديسكتوب.

## 5️⃣ إعداد Supabase للتحديثات (مرة واحدة)

1. اعمل مشروع جديد على [supabase.com](https://supabase.com) (مجاني)
2. افتح **SQL Editor** والصق محتوى ملف `supabase/migrations/001_updates.sql` واضغط Run
3. اعمل Bucket تخزين اسمه `barid-updates` (Public) من Storage
4. خد `Project URL` و `anon key` من Settings → API وحطهم في Secrets زي ما قلنا فوق

### إرسال تحديث/إصلاح للمستخدمين (أي وقت بعد كده)

1. ابني حزمة التحديث `.deb` بالتغييرات وارفعها على الـ Bucket (أو على GitHub Release)
2. أضف سطر في جدول `updates` (من Table Editor):

| version | channel | url | sha256 | changelog | active |
|---|---|---|---|---|---|
| 0.1.1 | stable | https://.../barid-update-0.1.1.deb | (حط الناتج ده) | إصلاح مشكلة كذا | ✔ |

عشان تجيب sha256: `sha256sum barid-update-0.1.1.deb`

كل الأجهزة اللي عليها BaridOS هتلاقي التحديث خلال 6 ساعات (أو فوراً بأمر `barid-update`).

## 6️⃣ المساعد الذكي "يساعدك"

- بعد أول إقلاع: افتح **يساعدك** من القائمة، أو في الترمنال: `yesaedak "سؤالك"`
- لو حابب تغيّر المفتاح بعدين: `yesaedak --set-key المفتاح_الجديد`
- لو عايز تتأكد إن الموديل شغال: `yesaedak --model gemini-3.5-flash-lite`
- الواجهة الرسومية: `yesaedak-gui`

## 7️⃣ أوامر سريعة (Terminal)

| الأمر | الوظيفة |
|---|---|
| `barid-panel` | فتح لوحة التحكم |
| `yesaedak "..."` | سؤال للمساعد الذكي |
| `barid-fps 60` | تحديد الفريمات لـ 60 (0 = بدون حد) |
| `barid-update` | فحص وتطبيق التحديثات فوراً |
| `nbfc set -s 70` | تثبيت المراوح على 70% يدوياً |

## ملاحظات صريحة

- **التحكم في مراوح اللابتوب** بيعتمد على موديل الجهاز: كتير من اللابتوبات بتتحكم في المراوح من الـ EC — بنستخدم `nbfc` ولو موديلك مش مدعوم الوضع التلقائي (thermald) لسه شغال عبر ACPI وبيقلل الحرارة بطريقة تانية (تقليل طاقة المعالج).
- **ماين كرافت** مش مدموجة في الـ ISO لأنها ملك Mojang — اللانشر PrismLauncher قانوني وبيحتاج حساب Microsoft.
- الحد الأقصى للـ Free Tier في Gemini: 1500 طلب/يوم لـ Flash-Lite — أكتر من كفاية لمساعد شخصي.
