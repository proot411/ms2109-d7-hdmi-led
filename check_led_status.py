#!/usr/bin/env python3
"""Read-only MS2109 LED diagnostics. No EEPROM/register writes.
HID SET_FEATURE sends B5 read requests only. Run on Linux as root.
"""
import argparse
import fcntl
import os
from pathlib import Path
import time


def read_byte(fd, address, command=0xB5):
    if command not in (0xB5, 0xE5):
        raise ValueError("Only XDATA and EEPROM read commands are allowed")
    request = bytearray([0, command, address >> 8, address & 255, 0, 0, 0, 0, 0])
    fcntl.ioctl(fd, 0xC0094806, request, True)
    response = bytearray(9)
    length = fcntl.ioctl(fd, 0xC0094807, response, True)
    if length == 8:
        response = bytearray([0]) + response[:8]
    elif length != 9:
        raise OSError(f"Unexpected HID response length: {length}")
    if response[:4] != request[:4]:
        raise OSError(f"HID echo mismatch: request={request.hex()} response={response.hex()}")
    return response[4]


def identify(fd):
    print('Read-only identification; HID command/address echoes are checked.', flush=True)
    for title, address, size, command in [
        ('Chip ID', 0xF800, 1, 0xB5),
        ('EEPROM header', 0, 16, 0xE5),
        ('Runtime header CBD0', 0xCBD0, 16, 0xB5),
        ('Runtime code CC00', 0xCC00, 16, 0xB5),
        ('Runtime LED area D1FB', 0xD1FB, 7, 0xB5),
    ]:
        data = bytes(read_byte(fd, address+i, command) for i in range(size))
        print(f'{title}: {data.hex(" ")}', flush=True)
    print('Expected A7 LED-build EEPROM header: a5 5a 07 bf 05 10 ff ff ff ff ff ff 20 20 07 07')
    print('Expected A7 LED-build code CC00: 02 ce 6e (then two mutable counter bytes)')
    print('No firmware or register changes were made.')


def d7_status(fd):
    chip=read_byte(fd,0xF800)
    if chip!=0xD7:
        raise SystemExit(f'D7 status requires chip ID d7; got {chip:02x}')
    print('Read-only D7 status; no writes. Keep HDMI state fixed for this run.', flush=True)
    print('Time  IRAM20 IRAM30 IRAM3F IRAM41 C740 C748  input-record-C71A', flush=True)
    start=time.monotonic()
    for _ in range(5):
        flags=[read_byte(fd,a) for a in [0x20,0x30,0x3F,0x41,0xC740,0xC748]]
        record=bytes(read_byte(fd,0xC71A+i) for i in range(21))
        print(f'{time.monotonic()-start:4.1f}  '+ ' '.join(f'{v:02x}' for v in flags)+'  '+record.hex(), flush=True)
        time.sleep(1)
    print('The timing record may retain the last mode after HDMI loss; it is not alone proof of signal lock.')


def d7_led(fd):
    if read_byte(fd,0xF800)!=0xD7:
        raise SystemExit('Expected D7 chip.')
    cfg=bytes(read_byte(fd,0xCBD0+i) for i in range(6))
    marker=bytes(read_byte(fd,0xCC04+i) for i in range(7))
    entry=bytes(read_byte(fd,0xCC00+i) for i in range(3))
    timer=bytes(read_byte(fd,0xCC30+i) for i in range(3))
    print('Runtime header:',cfg.hex(' '),'expected: 5a a5 02 00 09 10',flush=True)
    print('Build marker:',repr(marker),'expected: D7LED01',flush=True)
    if cfg!=bytes.fromhex('5aa502000910') or marker!=b'D7LED01' or entry!=bytes.fromhex('02cc80') or timer!=bytes.fromhex('02cc40'):
        raise SystemExit('D7 LED build is not loaded as expected. Do not interpret blink status.')
    print('PASS: D7 LED code and hooks loaded.',flush=True)
    print('Seconds  flags20  signal_absent  timer_phase  requested_LED',flush=True)
    start=time.monotonic()
    for _ in range(17):
        flag=read_byte(fd,0x20);phase=read_byte(fd,0xCC03)
        absent=bool(flag&16);on=not absent and phase<128
        print(f'{time.monotonic()-start:7.2f}  {flag:02x}       {int(absent)}              {phase:3}          {"ON" if on else "OFF"}',flush=True)
        time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', help='Specific /dev/hidrawN if more than one MS2109 is connected')
    parser.add_argument('--identify', action='store_true', help='Check chip revision, EEPROM header and running code only')
    parser.add_argument('--d7-status', action='store_true', help='Read D7 input timing and candidate status flags')
    parser.add_argument('--d7-led', action='store_true', help='Verify the D7LED01 runtime and sample its timer/signal status')
    args = parser.parse_args()
    candidates = []
    for node in sorted(Path('/sys/class/hidraw').glob('hidraw*')):
        fields = dict(line.split('=', 1) for line in (node/'device/uevent').read_text().splitlines() if '=' in line)
        ids = fields.get('HID_ID', '').split(':')
        if len(ids) == 3 and int(ids[1], 16) in (0x534D, 0x345F) and int(ids[2], 16) == 0x2109:
            candidates.append('/dev/' + node.name)
    if args.device:
        if args.device not in candidates:
            raise SystemExit('Requested device is not an identified 534d:2109 or 345f:2109 HID interface.')
        candidates = [args.device]
    if len(candidates) != 1:
        raise SystemExit(f'Expected one MS2109 HID interface; found {candidates}. Connect the capture card via USB, with programmer disconnected.')
    fd = os.open(candidates[0], os.O_RDWR | os.O_CLOEXEC)
    try:
        if args.d7_led:
            d7_led(fd)
            return
        if args.d7_status:
            d7_status(fd)
            return
        if args.identify:
            identify(fd)
            return
        # Ensure we are observing the intended code, not another firmware build.
        signature = bytes(read_byte(fd, 0xD1FB+i) for i in range(7))
        expected = bytes.fromhex('90c6aae030e061')
        print('Device:', candidates[0], 'chip ID:', hex(read_byte(fd, 0xF800)), flush=True)
        print('LED code signature:', signature.hex(), 'expected:', expected.hex(), flush=True)
        if signature != expected:
            raise SystemExit('LED routine signature differs. Stop here: firmware or read protocol needs checking.')
        print('Seconds  C6AA  valid  DE0C  counter  requested_LED', flush=True)
        start = time.monotonic()
        for _ in range(17):
            status = read_byte(fd, 0xC6AA)
            state = read_byte(fd, 0xDE0C)
            count = None
            for attempt in range(5):
                h1=read_byte(fd,0xCC04);lo=read_byte(fd,0xCC03);h2=read_byte(fd,0xCC04)
                if h1==h2:
                    count=h1*256+lo
                    break
            requested='OFF' if not status&1 else ('ON' if count is not None and count<32768 else 'OFF' if count is not None else '?')
            print(f'{time.monotonic()-start:7.2f}  {status:02x}    {status&1}     {state:02x}    {count!s:>5}    {requested}', flush=True)
            time.sleep(0.5)
    finally:
        os.close(fd)

if __name__=='__main__':
    try:
        main()
    except PermissionError:
        raise SystemExit('Permission denied. Run this script with sudo python3.')
    except OSError as error:
        raise SystemExit(f'HID read failed: {error}')
