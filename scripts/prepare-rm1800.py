#!/usr/bin/env python3
"""Pinned-source, experimental RM1800 build. No device flash operations."""
import pathlib
import subprocess
import sys

PIN = 'a151272502f075bfc5b708e8e696870aa2c48868'
root = pathlib.Path(sys.argv[1]).resolve()
assert subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip() == PIN

def replace(relative, old, new, count=1):
    file = root / relative
    text = file.read_text()
    assert text.count(old) == count, f'Unexpected source: {relative}: {old!r}'
    file.write_text(text.replace(old, new))

ath = 'package/kernel/mac80211/ath.mk'
replace(ath, '               select ATH11K_MEM_PROFILE_512M\n', '')
patch = 'package/kernel/mac80211/patches/nss/ath11k/207-ath11k-Enable-256_512MB-profiles.patch'
# Reuse the existing reduced 512M host rings for 256M, instead of falling
# through to the much larger default rings. Keep patch hunk line counts.
replace(patch, '+#ifdef CPTCFG_ATH11K_MEM_PROFILE_512M',
        '+#if defined(CPTCFG_ATH11K_MEM_PROFILE_512M) || defined(CPTCFG_ATH11K_MEM_PROFILE_256M)', count=2)
replace(patch, '+#define ATH11K_QMI_TARGET_MEM_MODE\tATH11K_QMI_TARGET_MEM_MODE_512M',
        '+#define ATH11K_QMI_TARGET_MEM_MODE\t(IS_ENABLED(CPTCFG_ATH11K_MEM_PROFILE_256M) ? ATH11K_QMI_TARGET_MEM_MODE_256M : ATH11K_QMI_TARGET_MEM_MODE_512M)')

dts = 'target/linux/qualcommax/files/arch/arm64/boot/dts/qcom/ipq6000-ax1800.dts'
replace(dts, 'qcom,ath11k-fw-memory-mode = <1>;', 'qcom,ath11k-fw-memory-mode = <2>;')
replace(dts, 'model = "Xiaomi AX1800";', 'model = "Xiaomi RM1800 (256MiB experimental)";')
# Keep xiaomi,ax1800 compatible/profile: matching upstream network,
# MAC, calibration and sysupgrade hooks; do not invent unsupported identity.
# Original factory ART is read only; no board-specific backup is uploaded.
base = root / 'target/linux/qualcommax/ipq60xx/base-files'
changed = []
for file in base.rglob('*'):
    if file.is_file():
        text = file.read_text()
        if '"0:art"' in text:
            file.write_text(text.replace('"0:art"', '"0:ART"'))
            changed.append(str(file.relative_to(root)))
assert changed, 'Expected ART partition name references missing'

# Preserve the upstream WCSS/TZ/NSS reserved-memory map. Reserve a small
# contiguous pool for DMA allocations; 8MiB is an experiment, not a proven fix.
kernel = root / 'target/linux/qualcommax/config-6.12'
options = {
    'CONFIG_CMA': 'y', 'CONFIG_DMA_CMA': 'y', 'CONFIG_CMA_SIZE_MBYTES': '8',
    'CONFIG_CMA_SIZE_SEL_MBYTES': 'y', 'CONFIG_CMA_SIZE_PERCENTAGE': '0',
    'CONFIG_CMA_SIZE_SEL_PERCENTAGE': None, 'CONFIG_CMA_SIZE_SEL_MIN': None,
    'CONFIG_CMA_SIZE_SEL_MAX': None, 'CONFIG_CMA_ALIGNMENT': '8',
    'CONFIG_CMA_AREAS': '8', 'CONFIG_CMA_DEBUGFS': None,
    'CONFIG_CMA_SYSFS': 'y', 'CONFIG_DMA_NUMA_CMA': None,
}
lines = kernel.read_text().splitlines()
lines = [line for line in lines if not any(
    line.startswith(key + '=') or line == '# ' + key + ' is not set'
    for key in options)]
settings = [key + '=' + value if value is not None else '# ' + key + ' is not set'
            for key, value in options.items()]
kernel.write_text('\n'.join(lines + settings) + '\n')

image = root / 'target/linux/qualcommax/image/ipq60xx.mk'
text = image.read_text()
start = text.index('define Device/xiaomi_ax1800\n')
end = text.index('\nendef', start)
block = text[start:end]
assert 'IMAGE_SIZE :=' not in block
text = text[:end] + '\n\tIMAGE_SIZE := 73728k' + text[end:]
image.write_text(text)

defaults = root / 'files/etc/uci-defaults/99-rm1800-lan'
defaults.parent.mkdir(parents=True, exist_ok=True)
defaults.write_text('''#!/bin/sh
uci set network.lan.ipaddr='192.168.1.1'
uci set network.lan.netmask='255.255.255.0'
uci set system.@system[0].hostname='RM1800-test'
uci commit network
uci commit system
exit 0
''')
defaults.chmod(0o755)
print('Applied experimental 256M host/FW profile, ART spelling and DMA pool changes.')
print('Calibration variant remains Xiaomi-AX1800; real hardware verification required.')
