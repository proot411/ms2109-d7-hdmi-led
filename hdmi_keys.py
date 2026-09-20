#!/usr/bin/env python3
"""Watch the tested D7LED01 HDMI flag; emit KP_1/KP_2 on an X11 desktop.
Keep OBS/VLC capturing: the firmware's signal flag can be stale while idle.
Default is dry-run. No firmware/register modifications are made.
"""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import time

from check_led_status import read_byte


class Debouncer:
    def __init__(self, delay=1.0):
        self.delay = delay
        self.stable = None
        self.candidate = None
        self.since = 0.0

    def update(self, present, now):
        if present != self.candidate:
            self.candidate, self.since = present, now
        if now - self.since < self.delay or present == self.stable:
            return None
        previous, self.stable = self.stable, present
        if previous is None:
            return None  # Establish baseline silently, including after USB reconnect.
        return 'KP_1' if present else 'KP_2'


def discover(device=None):
    found = []
    for node in sorted(Path('/sys/class/hidraw').glob('hidraw*')):
        try:
            fields = dict(line.split('=', 1) for line in
                          (node / 'device/uevent').read_text().splitlines() if '=' in line)
            ids = fields.get('HID_ID', '').split(':')
            if len(ids) == 3 and int(ids[1], 16) in (0x345F, 0x534D) and int(ids[2], 16) == 0x2109:
                found.append('/dev/' + node.name)
        except FileNotFoundError:
            continue
    if device:
        found = [p for p in found if p == device]
    if len(found) > 1:
        raise RuntimeError('Multiple cards found. Choose one with --device /dev/hidrawN.')
    return found[0] if found else None


def validate(fd):
    if read_byte(fd, 0xF800) != 0xD7:
        raise RuntimeError('This watcher requires the tested D7 chip.')
    for address, expected in [
        (0xCBD0, bytes.fromhex('5aa502000910')),
        (0xCC04, b'D7LED01'),
        (0xCC00, bytes.fromhex('02cc80')),
        (0xCC30, bytes.fromhex('02cc40')),
    ]:
        actual = bytes(read_byte(fd, address + i) for i in range(len(expected)))
        if actual != expected:
            raise RuntimeError('D7LED01 firmware verification failed; stopping without sending keys.')


def log(message):
    print(time.strftime('%H:%M:%S'), message, flush=True)


def send_key(executable, key):
    # xdotool splits this delay between press and release (about 150 ms held).
    # A default tap can fall between OBS's 25 ms hotkey polls.
    subprocess.run([executable, 'key', '--clearmodifiers', '--delay', '300', key],
                   check=True, timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--send-keys', action='store_true', help='Enable real KP_1/KP_2 events (default: log only)')
    parser.add_argument('--device', help='Choose a specific /dev/hidrawN')
    parser.add_argument('--test-key', choices=['KP_1', 'KP_2'],
                        help='Send one real key after five seconds, without reading HDMI')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as your desktop user, without sudo. Install the supplied HID permission rule first.')
    executable = None
    if args.send_keys or args.test_key:
        if os.environ.get('XDG_SESSION_TYPE') == 'wayland' or not os.environ.get('DISPLAY'):
            parser.error('Key output requires an X11 desktop session.')
        executable = shutil.which('xdotool')
        if not executable:
            parser.error('Install xdotool first: sudo apt install xdotool')
    if args.test_key:
        log(f'In five seconds, sending {args.test_key}. Click the OBS hotkey entry now.')
        time.sleep(5)
        send_key(executable, args.test_key)
        log(f'Sent test {args.test_key}.')
        return
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not runtime:
        parser.error('Start this from a terminal in your desktop session (XDG_RUNTIME_DIR is missing).')
    # Hold the lock for the full process lifetime; never unlink a live lock file.
    with open(Path(runtime) / 'ms2109-hdmi-keys.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another HDMI key watcher is already running.')
        log('Key output ENABLED.' if args.send_keys else 'DRY RUN: keys will only be logged.')
        log('Keep OBS/VLC capturing throughout. Idle signal status is unreliable.')
        fd = None
        debouncer = Debouncer()
        waiting = False
        try:
            while True:
                try:
                    if fd is None:
                        node = discover(args.device)
                        if node is None:
                            if not waiting:
                                log('Waiting for the capture card; no keys sent.')
                                waiting = True
                            time.sleep(1)
                            continue
                        fd = os.open(node, os.O_RDWR | os.O_CLOEXEC)
                        validate(fd)
                        debouncer = Debouncer()
                        waiting = False
                        log(f'{node}: verified firmware; establishing a silent baseline.')
                    present = not bool(read_byte(fd, 0x20) & 0x10)
                except PermissionError:
                    raise RuntimeError('HID access denied. Install 70-ms2109-hid.rules and reconnect USB.')
                except OSError as error:
                    if fd is not None:
                        os.close(fd)
                        fd = None
                    debouncer = Debouncer()
                    if not waiting:
                        log(f'USB/HID read unavailable ({error}); paused, no disconnect key sent.')
                    waiting = True
                    time.sleep(1)
                    continue
                previous = debouncer.stable
                key = debouncer.update(present, time.monotonic())
                if previous is None and debouncer.stable is not None:
                    log('Baseline: HDMI ' + ('present' if debouncer.stable else 'absent') + '; no key sent.')
                if key:
                    if executable:
                        # No --window: XTEST events reach normal desktop/global shortcut handling.
                        send_key(executable, key)
                    log(('Sent ' if executable else 'Would send ') + key +
                        (' — HDMI signal appeared' if present else ' — HDMI signal disappeared'))
                time.sleep(0.2)
        finally:
            if fd is not None:
                os.close(fd)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log('Stopped.')
    except (RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
