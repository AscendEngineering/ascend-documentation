#!/usr/bin/env python3
"""Install the adjacent Ascend 8TOF release using ST-Link and ST OpenOCD.
Python 3.9+, standard library only. See INSTALL.md for prerequisites.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

FLASH_BASE = 0x08000000
FLASH_SIZE = 0x100000
CONFIG_BASE = 0x080FC000
CONFIG_SIZE = 0x4000


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tcl(value):
    """Quote one Tcl word, including Windows paths and metacharacters."""
    value = str(value).replace('\\', '/')
    return '"' + value.replace('$', '\\$').replace('[', '\\[').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'


def read_values(output, name):
    match = re.search(r'^' + re.escape(name) + r'=([^\r\n]+)', output, re.M)
    if not match:
        raise RuntimeError('Missing target readback: ' + name)
    return [int(word, 0) for word in match.group(1).split()]


def load_release(root):
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest.get('schema') != 1 or manifest.get('board') != 'horizontal-v3':
        raise RuntimeError('Unsupported release manifest / board.')
    # Fixed filenames and addresses: never trust a manifest to pick a write address.
    image = root / 'firmware.bin'
    size = image.stat().st_size
    if size < 256 or size > CONFIG_BASE - FLASH_BASE:
        raise RuntimeError('Firmware size overlaps configuration or is implausible.')
    if size != manifest['firmware_size'] or sha256(image) != manifest['firmware_sha256']:
        raise RuntimeError('Firmware checksum/size mismatch. Download and extract the complete release again.')
    vector = image.read_bytes()[:8]
    sp, pc = (int.from_bytes(vector[i:i+4], 'little') for i in (0,4))
    if not (0x20000000 < sp <= 0x200A0000 and FLASH_BASE <= (pc & ~1) < FLASH_BASE+size and pc & 1):
        raise RuntimeError('Invalid STM32H563 firmware vector table.')
    return manifest


def locate_openocd(explicit):
    if explicit:
        found = shutil.which(explicit) or (explicit if Path(explicit).is_file() else None)
        if not found:
            raise RuntimeError('OpenOCD executable not found: ' + explicit)
        return Path(found).resolve()
    found = shutil.which('openocd')
    if found:
        return Path(found).resolve()
    # Optional discovery of the ST OpenOCD bundled with STM32CubeIDE.
    patterns = [
        '/Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.openocd.*/tools/bin/openocd',
        '/opt/st/stm32cubeide_*/plugins/com.st.stm32cube.ide.mcu.externaltools.openocd.*/tools/bin/openocd',
        'C:/ST/STM32CubeIDE_*/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.openocd.*/tools/bin/openocd.exe',
    ]
    import glob
    for pattern in patterns:
        candidates = sorted(glob.glob(pattern), reverse=True)
        if candidates:
            return Path(candidates[0])
    raise RuntimeError('ST OpenOCD was not found. See INSTALL.md, then supply --openocd PATH and --scripts PATH.')


def locate_scripts(exe, explicit):
    candidates = [Path(explicit)] if explicit else [
        exe.parent.parent / 'share/openocd/scripts',
        exe.parent.parent / 'scripts',
    ]
    if not explicit:
        # STM32CubeIDE can keep ST scripts in a separate debug plugin.
        for parent in exe.parents:
            if parent.name == 'plugins':
                candidates.extend(sorted(parent.glob('com.st.stm32cube.ide.mcu.debug.*/resources/openocd/st_scripts'), reverse=True))
    for candidate in candidates:
        if (candidate/'target/stm32h5x.cfg').is_file() and (candidate/'interface/stlink-dap.cfg').is_file():
            return candidate.resolve()
    raise RuntimeError('OpenOCD scripts with STM32H5 + stlink-dap support not found. Supply --scripts PATH; stock OpenOCD 0.12 may lack STM32H5.')


class Installer:
    def __init__(self, root, exe, scripts, serial, output):
        self.root, self.exe, self.scripts = root, exe, scripts
        self.serial, self.output = serial, output

    def run(self, stage, commands):
        script = self.output / (stage + '.tcl')
        script.write_text(commands, encoding='utf-8')
        cmd = [str(self.exe), '-s', str(self.scripts)]
        if self.serial:
            cmd += ['-c', 'set ASCEND_STLINK_SERIAL ' + tcl(self.serial)]
        cmd += ['-f', str(self.root/'openocd-horiz3.cfg'), '-f', str(script)]
        print(stage.replace('-', ' ').capitalize() + '...', flush=True)
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, errors='replace', timeout=180)
        except subprocess.TimeoutExpired as exc:
            raw = exc.stdout or b''
            text = raw.decode(errors='replace') if isinstance(raw, bytes) else raw
            (self.output/(stage+'.log')).write_text(text, encoding='utf-8')
            raise RuntimeError('OpenOCD timed out. Keep the backup; check power/cable and logs before retrying.') from exc
        (self.output/(stage+'.log')).write_text(result.stdout, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('OpenOCD failed during ' + stage + ':\n' + result.stdout[-2500:])
        return result.stdout


def target_guard(uid=None):
    guard = '''init
halt
wait_halt 2000
set chip [read_memory 0x44024000 32 1]
if {([lindex $chip 0] & 0xfff) != 0x484} { resume; error "Expected STM32H56/H57 device" }
set uid [read_memory 0x08fff800 32 3]
echo "UID=$uid"
'''
    if uid:
        condition = ' || '.join('[lindex $uid %d] != 0x%08x' % (i,word) for i,word in enumerate(uid))
        guard += 'if {' + condition + '} { resume; error "Board changed since identification" }\n'
    return guard


def verify_profile(output, manifest):
    for name, spec in manifest['readback'].items():
        values = read_values(output, name)
        if 'expected' in spec and values != spec['expected']:
            raise RuntimeError('Firmware was written, but sensor verification failed: %s=%s. See INSTALL.md.' % (name, values))
    return {name: read_values(output, name) for name in manifest['readback']}


def install(args, root):
    manifest = load_release(root)
    print('Ascend 8TOF %s: horizontal v3, 8x8, 10 Hz, 10 ms' % manifest['version'])
    print('Firmware SHA-256: ' + manifest['firmware_sha256'])
    if args.check:
        print('Package integrity OK. No hardware accessed.')
        return 0
    exe = locate_openocd(args.openocd or os.environ.get('OPENOCD'))
    scripts = locate_scripts(exe, args.scripts or os.environ.get('OPENOCD_SCRIPTS'))
    if args.board != 'horizontal-v3':
        raise RuntimeError('Specify --board horizontal-v3 after confirming the physical board. MCU identity cannot identify the PCB revision.')
    parent = Path(args.backup_dir).expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix=dt.datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=parent))
    print('Backup and logs: ' + str(output))
    tool = Installer(root, exe, scripts, args.serial, output)
    probe = tool.run('identify', target_guard() + 'flash probe 0\necho "FLASH_BANKS=[flash banks]"\nresume\nshutdown\n')
    uid = read_values(probe, 'UID')
    # Reject non-1-MiB layouts before reading or modifying flash. TrustZone or
    # protected devices must be configured separately; never unlock or regress.
    if not re.search(r'0x08000000, size 0x00100000', probe):
        raise RuntimeError('Expected a 1 MiB non-secure flash bank. Device protection/layout is unsupported; see identify.log.')
    print('Board UID: ' + '-'.join('%08x' % word for word in uid))
    if not args.yes:
        print('This writes firmware and resets the board. Saved masks will be preserved. Disconnect it from a flying/armed vehicle.')
        if input('Type INSTALL to continue: ').strip() != 'INSTALL':
            print('Cancelled. No flash was changed.')
            return 0
    backup = output/'before-flash.bin'
    tool.run('backup', target_guard(uid) + 'dump_image %s 0x08000000 0x100000\nresume\nshutdown\n' % tcl(backup))
    if backup.stat().st_size != FLASH_SIZE:
        raise RuntimeError('Incomplete backup; refusing to flash.')
    config = backup.read_bytes()[-CONFIG_SIZE:]
    (output/'before-config.bin').write_bytes(config)
    # Staging the checked image inside the backup directory fixes which bytes
    # are programmed even if someone replaces the downloaded package later.
    staged = output/'installed-firmware.bin'
    shutil.copyfile(root/'firmware.bin', staged)
    if sha256(staged) != manifest['firmware_sha256']:
        raise RuntimeError('Firmware changed after validation; refusing to flash.')
    flashed = tool.run('flash', target_guard(uid) +
        'reset init\nflash write_image erase %s 0x08000000 bin\nverify_image %s 0x08000000 bin\necho "** Verified OK **"\nreset run\nshutdown\n' % (tcl(staged), tcl(staged)))
    if '** Verified OK **' not in flashed:
        raise RuntimeError('OpenOCD did not confirm programming verification. Check flash.log.')
    cmds = 'init\nsleep 12000\nhalt\nwait_halt 2000\n'
    cmds += 'set uid [read_memory 0x08fff800 32 3]\n'
    condition = ' || '.join('[lindex $uid %d] != 0x%08x' % (i,word) for i,word in enumerate(uid))
    cmds += 'if {' + condition + '} { resume; error "Board changed after flash" }\n'
    for name, spec in manifest['readback'].items():
        address = int(spec['address'],0)
        if not 0x20000000 <= address < 0x200A0000 or spec['bits'] not in (8,32) or not 1 <= spec['count'] <= 8:
            raise RuntimeError('Invalid diagnostic address in manifest.')
        cmds += 'echo "%s=[read_memory 0x%08x %d %d]"\n' % (name,address,spec['bits'],spec['count'])
    cmds += 'dump_image %s 0x080fc000 0x4000\n' % tcl(output/'after-config.bin')
    cmds += 'dump_image %s 0x08000000 %d\nresume\nshutdown\n' % (tcl(output/'firmware-readback.bin'),manifest['firmware_size'])
    output_text = tool.run('verify-sensors', cmds)
    if (output/'after-config.bin').read_bytes() != config:
        raise RuntimeError('Saved mask changed unexpectedly. Original is in before-config.bin; keep this backup.')
    if sha256(output/'firmware-readback.bin') != manifest['firmware_sha256']:
        raise RuntimeError('Firmware readback checksum mismatch.')
    readback = verify_profile(output_text, manifest)
    report = {'version':manifest['version'], 'uid':uid, 'firmware_sha256':manifest['firmware_sha256'],
              'backup_sha256':sha256(backup), 'configuration_preserved':True,'readback':readback}
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('SUCCESS: flash verified; all 8 sensors at 10 Hz / 10 ms; saved masks preserved.')
    print('Backup and verification report: ' + str(output))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true', help='Validate the package without touching hardware')
    p.add_argument('--board', choices=['horizontal-v3'])
    p.add_argument('--openocd', help='Path to ST OpenOCD executable')
    p.add_argument('--scripts', help='OpenOCD scripts directory containing target/stm32h5x.cfg')
    p.add_argument('--serial', help='ST-Link probe serial number (otherwise connect only one probe)')
    p.add_argument('--backup-dir', default=str(Path.home()/'Ascend8TOF'/'backups'))
    p.add_argument('--yes', action='store_true', help='Skip the interactive INSTALL prompt')
    args = p.parse_args(argv)
    try:
        return install(args, Path(__file__).resolve().parent)
    except (RuntimeError, OSError, ValueError, KeyError, EOFError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
