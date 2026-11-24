#!/bin/bash
# BaridOS ISO build script — runs on a Debian/Ubuntu machine or CI runner
set -euo pipefail

echo "=== [1/5] Installing build dependencies ==="
apt-get update
apt-get install -y --no-install-recommends \
    live-build live-config live-boot \
    debootstrap xorriso isolinux syslinux-efi \
    squashfs-tools procps mtools dosfstools

echo "=== [2/5] Preparing live-build tree ==="
rm -rf build-work
mkdir -p build-work
cd build-work

# Copy config (package lists, hooks, chroot includes)
cp -r ../config/* config/ 2>/dev/null || true
cp -r ../build/config/* config/

# Bake BaridOS apps into /opt/barid
mkdir -p config/includes.chroot/opt/barid
cp -r ../system/barid-* config/includes.chroot/opt/barid/

# Optional secrets injection (never commit these to git!)
if [ -n "${BARID_AI_KEY:-}" ]; then
    cat > config/includes.chroot/etc/barid/ai.conf <<EOF
{
  "api_key": "${BARID_AI_KEY}",
  "model": "${BARID_AI_MODEL:-gemini-3.5-flash-lite}"
}
EOF
    echo "I: Gemini API key baked into /etc/barid/ai.conf"
fi
if [ -n "${SUPABASE_URL:-}" ] && [ -n "${SUPABASE_ANON_KEY:-}" ]; then
    cat > config/includes.chroot/etc/barid/update.conf <<EOF
{
  "supabase_url": "${SUPABASE_URL}",
  "supabase_anon_key": "${SUPABASE_ANON_KEY}"
}
EOF
    echo "I: Supabase config baked into /etc/barid/update.conf"
fi

echo "=== [3/5] lb config ==="
mkdir -p auto
cp ../build/auto/config auto/config
lb config

echo "=== [4/5] lb build (this takes 20-60 min) ==="
lb build

echo "=== [5/5] Renaming output ==="
ISO=$(ls *.iso | head -n1)
VERSION=$(cat config/includes.chroot/opt/barid/VERSION 2>/dev/null || echo "0.1.0")
mv "$ISO" "baridos-${VERSION}-amd64.iso"
sha256sum "baridos-${VERSION}-amd64.iso" > "baridos-${VERSION}-amd64.iso.sha256"

echo ""
echo "DONE: baridos-${VERSION}-amd64.iso"
ls -lh baridos-*.iso*
