-- BaridOS update system — Supabase schema
-- شغّل هذا الملف في SQL Editor في مشروع Supabase

create table if not exists public.updates (
    id uuid primary key default gen_random_uuid(),
    version text not null,
    channel text not null default 'stable',
    url text not null,               -- رابط حزمة .deb (رفعها على Supabase Storage أو GitHub Release)
    sha256 text,                     -- توقيع التحقق
    changelog text default '',
    active boolean default true,
    created_at timestamptz default now()
);

-- فهرس للبحث السريع
create index if not exists updates_channel_active_idx
    on public.updates (channel, active, version desc);

-- أي حد يقدر يقرأ التحديثات (الجدول عام القراءة فقط)
alter table public.updates enable row level security;

create policy "public read updates"
    on public.updates for select
    using (true);

-- الكتابة (إرسال تحديث جديد) تتم فقط من Dashboard أو بمفتاح service_role
-- لا تضف policy للكتابة بالمفتاح anon.

-- إدراج أول تحديث تجريبي:
insert into public.updates (version, url, sha256, changelog)
values ('0.1.0', 'https://example.com/barid-update-0.1.0.deb', null, 'الإصدار الأول');

-- ------- Supabase Storage (اختياري لتخزين الحزم) -------
-- 1) أنشئ Bucket جديد اسمه: barid-updates  (Public)
-- 2) ارفع ملف .deb عليه
-- 3) خده الرابط العام وحطه في عمود url
insert into storage.buckets (id, name, public)
values ('barid-updates', 'barid-updates', true)
on conflict (id) do nothing;

create policy "public read barid-updates"
    on storage.objects for select
    using (bucket_id = 'barid-updates');
