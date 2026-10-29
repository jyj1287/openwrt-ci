# RM1800 / 256MiB experimental build

This build is NOT hardware verified. A successful Actions run confirms compilation,
not Wi-Fi calibration, safe flashing, or runtime stability.

Known device: Xiaomi RM1800, 256MiB physical RAM, 128MiB NAND, 2048-byte pages,
128KiB eraseblocks. Existing AX5 MIBIB rootfs is 72MiB at 0x1180000. No bootloader,
MIBIB, CDT, ART, bdata, MAC addresses or device backups are included or rewritten.

Source: LiBwrt/openwrt-6.x at a151272502f075bfc5b708e8e696870aa2c48868
(25.12-nss at preparation time). Kernel family 6.12. Feeds are resolved at build
time and their revisions are recorded; feeds are not fully pinned in this draft.

The upstream xiaomi_ax1800 profile and compatible are retained for existing board
scripts. Model label identifies the RM1800 experiment; this does not establish
native upstream RM1800 support. Calibration variant is Xiaomi-AX1800, not Redmi-AX5.
Runtime validation of the board data and per-device ART is still required.

Changes: select 256M firmware mode, remove NSS's forced 512M selection, make the
existing reduced host ring profile apply to 256M as well; preserve protected RAM
regions, request an 8MiB CMA DMA pool, correct ART partition spelling for this
device, and omit optional services. CMA availability and host memory budgets must
be checked in the generated kernel config and on hardware. These are hypotheses
to test against the observed 2MiB DMA allocation failure, not a proven remedy.

Management IP is 192.168.1.1. Set a root password locally after boot.
There is no embedded private credential or shared default password.

Upload these four added files to the fork, preserving their paths. On the default
branch, open Actions, enable fork workflows if GitHub requests it, select
RM1800-256-EXPERIMENTAL, and run manually. No scheduled builds or releases are added.
Download the run's artifact, not an unrelated workflow's Releases.

Before any flash, inspect build.config, generated kernel config, firmware hashes,
FIT configuration/load addresses, DT reserved RAM and actual UBI geometry. Prefer
a verified initramfs RAM test. Do not apply the previous image's CRC or byte count
to these new images. Keep the known U-Boot recovery and old transition image.
Do not alter CDT to claim 512MiB physical RAM.

After a test boot, verify uname, /proc/cmdline, MemTotal/CmaTotal/CmaFree,
/proc/buddyinfo, ath11k/remoteproc logs, both Wi-Fi PHYs, calibration and Ethernet.
The temporary U-Boot module_blacklist used during recovery must be removed for an
actual Wi-Fi test, otherwise no wireless driver will load.
