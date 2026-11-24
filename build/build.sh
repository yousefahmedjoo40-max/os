#!/bin/bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo ./build/build.sh" >&2
  exit 1
fi

echo "=== [1/5] Installing build dependencies ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  live-build live-config live-boot debootstrap xorriso isolinux syslinux-efi \
  squashfs-tools mtools dosfstools procps ca-certificates coreutils gnupg

echo "=== [2/5] Preparing clean build tree ==="
cd "$(dirname "$0")/.."
rm -rf build-work
mkdir -p build-work
cd build-work

cp -r ../config/* config/ 2>/dev/null || true
cp -r ../build/config/* config/

mkdir -p config/archives
cat > config/archives/baridos.list.binary <<'EOF'
deb https://deb.debian.org/debian trixie main contrib non-free non-free-firmware
deb https://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware
deb https://deb.debian.org/debian-security trixie-security main contrib non-free non-free-firmware
EOF
cat > config/archives/baridos.list.chroot <<'EOF'
deb https://deb.debian.org/debian trixie main contrib non-free non-free-firmware
deb https://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware
deb https://deb.debian.org/debian-security trixie-security main contrib non-free non-free-firmware
EOF

mkdir -p config/includes.chroot/opt/barid
cp -r ../system/barid-* config/includes.chroot/opt/barid/ 2>/dev/null || true

if [[ -n "${BARID_AI_KEY:-}" ]]; then
  mkdir -p config/includes.chroot/etc/barid
  cat > config/includes.chroot/etc/barid/ai.conf <<EOF
{
  "api_key": "${BARID_AI_KEY}",
  "model": "${BARID_AI_MODEL:-gemini-3.5-flash-lite}"
}
EOF
fi

if [[ -n "${SUPABASE_URL:-}" && -n "${SUPABASE_ANON_KEY:-}" ]]; then
  mkdir -p config/includes.chroot/etc/barid
  cat > config/includes.chroot/etc/barid/update.conf <<EOF
{
  "supabase_url": "${SUPABASE_URL}",
  "supabase_anon_key": "${SUPABASE_ANON_KEY}"
}
EOF
fi

echo "=== [3/5] Cleaning live-build state ==="
lb clean --purge >/dev/null 2>&1 || true
rm -rf cache chroot binary chroot.packages binary.packages config/bootstrap config/common config/binary

mkdir -p auto
cp ../build/auto/config auto/config

# The build now runs as Debian 13, so Debian mirrors and keyrings are used explicitly.
sed -i '/--debootstrap-options/d' auto/config
sed -i '/^[[:space:]]*--image-name/i\    --mirror-bootstrap "https://deb.debian.org/debian/" \
    --mirror-binary "https://deb.debian.org/debian/" \
    --mirror-chroot "https://deb.debian.org/debian/" \
    --mirror-chroot-security "https://deb.debian.org/debian-security/" \\' auto/config

PACKAGE_LIST="config/package-lists/barid.list.chroot"
if [[ -f "$PACKAGE_LIST" ]] && ! grep -qxF coreutils "$PACKAGE_LIST"; then
  sed -i '/^# --- Base system ---$/a coreutils\ngnupg' "$PACKAGE_LIST"
fi

echo "=== [4/5] Running lb build ==="
lb config
lb build 2>&1 | tee build.log

echo "=== [5/5] Renaming output ==="
ISO=$(ls -1 live-image-amd64.hybrid.iso 2>/dev/null || ls -1 *.iso 2>/dev/null | head -n1)
if [[ -z "${ISO:-}" ]]; then
  echo "ISO build failed; inspect build-work/build.log" >&2
  exit 1
fi
VERSION=$(cat config/includes.chroot/opt/barid/VERSION 2>/dev/null || echo "0.1.0")
FINAL="baridos-${VERSION}-amd64.iso"
mv "$ISO" "$FINAL"
sha256sum "$FINAL" > "${FINAL}.sha256"

echo "DONE: $FINAL"
ls -lh "$FINAL" "${FINAL}.sha256"
