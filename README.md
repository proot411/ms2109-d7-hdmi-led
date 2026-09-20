# MS2109 D7 HDMI signal LED

Documented 2026-09-21 for proot's tested USB 2.0 HDMI capture board.

Project by **proot**. Shell examples below run from the root of this repository unless a different working directory is shown. Replace `/home/proot` in the programmer-tool example with your own home directory.


A visible indication of whether a cheap USB HDMI capture card is receiving video, with an optional Linux script that triggers actions when the signal appears or disappears.

The original use case was an NVR whose output selection could make capture lag, and a card with no useful visible indication of incoming video. This project adds an LED to the board's existing D3 footprint, makes it blink while the tested signal flag reports video, and exposes the same status to a desktop watcher. The watcher can switch application behavior using numpad 1 and numpad 2 shortcuts.

**Tested:** this specific MS2109S-marked board, D7 chip ID, MS24C16 EEPROM, CH341A programmer, and a Linux X11 desktop. **Important:** keep capture active in OBS or VLC. When capture is idle, the card can report stale status and blink even with no HDMI connected. This project does not resolve that firmware limitation.

## Demonstrations

### Capture-card test

![Capture-card demonstration with the modified board shown in the inset](images/capture_card_test.gif)

`capture_card_test.gif` shows the capture test with the modified board visible in the inset. The animation is a demonstration, not a calibrated measurement of blink rate, frame rate or latency.

### OBS source test

![OBS source and HDMI keybind demonstration](images/obs_source_test.gif)

`obs_source_test.gif` shows the host-side source test. The Linux watcher sends synthetic numpad events; OBS itself was not modified. Bind those keys to the desired actions in your application.

## Board and wiring gallery

All media embedded in this README comes from this repository's `images/` folder. Photos and recordings document the user's particular board; visually similar products can contain a different revision.

### Capture-card product reference

![USB HDMI capture-card product reference](images/usb_capture_card.png)

The supplied product-reference screenshot helps identify the general enclosure style. Its marketing claims are not specifications verified by this project.

### Opened PCB

![Capture-card PCB before the LED modification](images/usb_capture_card_pcb.jpg)

The processor, external EEPROM, HDMI connector and USB wiring are visible on the board.

### Processor marking

![MS2109S marking on the capture processor](images/MS2109S.jpg)

The package marking is MS2109S; the D7 target identification comes from the live HID chip-ID read, not from the package name alone.

### Pinout reference

![MS2109S pinout reference supplied with the project](images/MS2109S_pinout.png)

The supplied pinout image is a reference for tracing the user's board. It is not an original diagram authored by this project. Confirm package orientation and continuity before using a numbered pin.

### External EEPROM

![MS24C16 EEPROM on the board](images/EEPROM.jpg)

This is the storage chip programmed with the CH341A. The capture processor's internal mask ROM is not rewritten.

### LED connection detail

![Annotated D3 LED connection and GPIO0 location](images/LED.jpg)

The supplied annotation identifies the D3 area, GPIO0/pin 39 and the supply path. Confirm the approximately 980-ohm series resistance and polarity on your own board rather than assuming every clone uses the same layout.

### Assembled modification

![Modified capture board with the installed LED](images/kinda_finish_product.jpg)

The assembled board is the hardware used for the reported LED and keybind tests.

## Authorship and scope

**The custom D7 LED patch, image builder, diagnostic scripts, keybind watcher, and this README were produced by OpenAI's ChatGPT/Codex assistant for proot during this project.** They were developed using the independent upstream research and tools credited below. proot supplied the board, original image, photographs, continuity/voltage measurements and live diagnostic results; performed the soldering and CH341A flashing; and confirmed the LED and numpad keybindings worked. The assistant did not physically program or test the board itself.

This is a board-tested custom patch, not official MacroSilicon firmware or a claim of authorship over upstream research, code or mask ROM. Upstream licenses and attribution remain applicable. This repository packages the working D7 build and host tools. Renaming the binary does not change its contents or flash checksum.

## Hardware and files

| Item | This project |
| --- | --- |
| Capture processor | MacroSilicon MS2109 family, **D7 revision**; HID read at `0xF800` returned `0xD7` |
| Capture USB identity | `345f:2109` on this board |
| Chip physically programmed | External **MS24C16 I²C EEPROM**, 16 Kbit / 2048 bytes |
| Programmer | CH341A, USB identity `1a86:5512`, EPP/MEM/I²C mode |
| Working image | `ms2109_d7_led_v1.bin`, 2048 bytes |
| Firmware marker | `D7LED01` |
| LED connection | D3, active-low GPIO0, reported by the user as chip pin 39 |

The CH341A writes the EEPROM, not the processor's permanent mask ROM. At startup, the processor's ROM loads the EEPROM patch into RAM and calls its enabled hooks. The firmware architecture and HID interface are described in [amnemonic/MacroSilicon](https://github.com/amnemonic/MacroSilicon); the D7-specific layout was checked against [NKTKLN/ms2109-d7-1024x600](https://github.com/NKTKLN/ms2109-d7-1024x600).

## Repository contents

```text
ms2109_d7_led_v1.bin  Ready-to-flash, verified 2048-byte image
firmware.asm              D7 hook code and embedded display descriptor
build_image.py            EEPROM image/checksum builder
check_led_status.py   Read-only device diagnostics
hdmi_keys.py          Debounced HDMI-to-numpad watcher for X11
70-ms2109-hid.rules     Local desktop user access to the card's HID node
test_hdmi_keys.py       Hardware-free watcher tests
images/                      Board photos, pinout and two demo GIFs
SHA256SUMS                   Published firmware checksum
```

The published binary contains the working LED patch and display configuration. Its shorter filename is an organizational change, not a different firmware build. Original backups, failed prototype images, compiled scratch files, and third-party ROM dumps are not included.

Earlier A7-format LED images from development were **not the successful D7 build** and are excluded from this repository. The earlier image could be read back from EEPROM but its intended code was not found at the expected runtime addresses. D7 identification and the reference ROM led to a replacement D7-compatible patch. An EEPROM write verification alone does not establish that the processor loaded the patch.

Working image SHA-256:

```text
3101e40ffa25133b350a7a6d94248b513af5c3fd01f2d07f7752a455f6b121fd
```

## How the LED works

The board's D3 positive pad was traced through an approximately 980 Ω resistor to its supply; the other pad was traced to GPIO0. The user installed the LED. The earlier suspected DVDD12 connection was a measurement mistake and must not be used as wiring guidance. Retain the verified series resistor; check the actual traces on any different board.

GPIO0 is controlled through `P2.0`; clearing `P3.0` enables its output on this D7 implementation. The LED is active-low: a low GPIO level sinks current and turns it on; a high level turns it off. GPIO background research came from [BertoldVdb/ms-tools](https://github.com/BertoldVdb/ms-tools/blob/main/mshal/hal_patch_gpio.go), with D7 behavior checked against the reference ROM and this board's observations.

The patch adds a private 8-bit timer phase at RAM address `0xCC03`. The timer hook preserves the original D7 timer body's three 16-bit counter increments and `0xF005` acknowledgement, then increments this private phase. It does not add a delay loop or reconfigure the timer. The normal hook reads the phase's top bit and reapplies the LED output after ROM activity.

The observed signal flag is **IRAM byte `0x20`, bit 4**, mask `0x10`. When this bit is set, the patch forces the LED off. When clear, phase values 0–127 request LED on and 128–255 request LED off. This mapping is supported by proot's live connected/disconnected measurements while capture was active, not a guarantee for every MS2109 revision.

The captured diagnostic samples advanced by about 50 counts per half second. That suggests approximately 100 timer ticks per second, 1.28 seconds per half-cycle, and 2.56 seconds per complete blink. This is an estimate from host samples, not a calibrated frequency specification.

### States exposed to the host

| Condition while capture is active | Observed `flags20` | `flags20 & 0x10` | Interpretation | LED request | Watcher event after a stable change |
| --- | --- | --- | --- | --- | --- |
| HDMI video present | `0x84` | `0x00` | Signal present | Alternates on/off with phase | `KP_1` / numpad 1 |
| HDMI video absent | `0x94` | `0x10` | Signal absent | Off | `KP_2` / numpad 2 |
| USB/HID unavailable | No valid reading | Unknown | Unknown, not HDMI loss | Host cannot establish it | None; watcher pauses |
| First stable reading | Either | Either | Establish baseline | Firmware controls LED | None |

Only bit 4 is interpreted; do not require the entire byte to equal `0x84` or `0x94`. The LED does not itself output keyboard events. The Python watcher reads the flag over HID and separately asks the desktop to generate keys. The diagnostic's `requested_LED` column is calculated from flag and phase, not an electrical readback of the LED pin.

**Known limitation:** with OBS/VLC closed or otherwise not capturing, the flag may be stale or misleading. The user observed blinking with no HDMI attached while capture was idle. Keep capture active for reliable use of this tested flag. The timing record at `0xC71A` also retained its previous mode after HDMI loss, so it is not used as proof of current signal. This detects the reported video signal state, not whether a physical cable is plugged in or whether the picture is black.

### Patch layout and identification

| Location | Value / purpose |
| --- | --- |
| EEPROM bytes 0–1 | `5A A5`, D7 image magic |
| EEPROM bytes 2–3 | `02 00`, 512-byte payload |
| EEPROM bytes 4–5 | `09 10`, hook enable and EDID feature gate |
| EEPROM payload offset | `0x30`; loaded at `0xCC00` |
| `0xCC00` | `02 CC 80`, jump to normal hook |
| `0xCC03` | Mutable phase counter |
| `0xCC04` | ASCII `D7LED01` |
| `0xCC30` | `02 CC 40`, jump to timer hook |
| `0xCD00` | 256-byte EDID |
| Runtime header `0xCBD0` | Starts `5A A5 02 00 09 10` |

D7 event 8 supplies the EDID through the ROM routine at `0x73F7`. The image uses reference header configuration bytes `18 09 06 11` at offsets 12–15 because this board's original factory D7 header was unavailable. No complete donor executable payload was imported; the patch does reproduce the original ROM timer-body behavior and depends on specific ROM addresses. Do not assume these addresses apply to A7 or other chips.

## Resolution behavior

The custom EDID advertises 1280×720 at 60 Hz as the video mode, to encourage sources such as the NVR to choose 720p instead of a higher-resolution mode. The patch also sets UVC default frame index 6 in the relevant MJPEG/YUYV descriptors. These are separate input-advertisement and host-default changes; they do not force every source or application to comply.

Select MJPEG, 1280×720, 60 fps in the capture application if available. The EEPROM does not guarantee 60 unique captured frames per second, eliminate all latency, or convert a slower source into true 60 fps. Reconnect or restart a source that cached the previous EDID.

## Building the image

With SDCC's assembler/linker and binary conversion tools installed, build in a separate directory:

```bash
mkdir -p build
cp firmware.asm build_image.py build/
cd build
sdas8051 -lo firmware.rel firmware.asm
sdld -nui -b HOME=0xCC00 -i firmware.ihx firmware.rel
sdobjcopy -I ihex -O binary firmware.ihx firmware.bin
python3 build_image.py
cmp ms2109_d7_led_v1.bin ../ms2109_d7_led_v1.bin
cd ..
```

The builder writes a 2048-byte image, places the 512-byte payload after the 48-byte header, appends the header/payload additive checksums, and checks both EDID block checksums. The recorded build was checked with an opcode interpreter across all 256 timer phases, both signal states, event routing, register preservation and GPIO bit isolation. The user subsequently confirmed runtime loading and actual blinking on the board. These firmware execution checks were performed during development against the reference ROM; the ROM and research workspace are not redistributed here. The included test suite covers the host watcher.

## Flashing with the CH341A on Linux

The tool used was [command-tab/ch341eeprom](https://github.com/command-tab/ch341eeprom), locally at `/home/proot/Documents/ch341-tools/ch341eeprom`. It uses libusb; `1a86:5512` appearing in `lsusb` is the relevant programmer detection, not a serial-port device.

The user used soldered connections because the clip was unreliable. Disconnect the capture card's USB and HDMI before programming, and disconnect the programmer and its wiring before normal USB operation. Verify programmer voltage, ground and the EEPROM's SDA/SCL/VCC connections for the board; this README does not infer safe CH341A electrical levels from the adapter's appearance. The CH341A must use its 24-series I²C connections, not an assumed SPI layout.

First preserve two matching 2048-byte backups under new filenames (do not overwrite an existing recovery backup):

```bash
cd /home/proot/Documents/ch341-tools/ch341eeprom
sudo ./ch341eeprom -s 24c16 -c 0 -r before-change-1.bin
sudo ./ch341eeprom -s 24c16 -c 0 -r before-change-2.bin
cmp before-change-1.bin before-change-2.bin
wc -c before-change-1.bin
```

Use `-c 0` **after** `-s 24c16`, matching the successful procedure for this installed tool. Earlier reads without the corrected selection returned the wrong header despite matching each other. Matching reads establish repeatability, not by themselves correct addressing; inspect the header and preserve a known-good backup.

Write the working image and independently read it back:

```bash
fw="/absolute/path/to/ms2109-d7-hdmi-led/ms2109_d7_led_v1.bin"
wc -c "$fw"
sha256sum "$fw"
sudo ./ch341eeprom -s 24c16 -c 0 -w "$fw"
sudo ./ch341eeprom -s 24c16 -c 0 -r d7-led-readback.bin
cmp "$fw" d7-led-readback.bin && echo "VERIFIED"
xxd -l 16 d7-led-readback.bin
```

Expected first 16 bytes:

```text
5a a5 02 00 09 10 ff ff ff ff ff ff 18 09 06 11
```

No separate erase was used. A “Wrote 2048 bytes” message alone is insufficient. In this project an initial comparison failed at byte 1; after the user resoldered the connections, the readback matched and printed `VERIFIED`. Do not treat a failed comparison as a successful flash.

After disconnecting the programmer, power the card normally by USB. Return to the repository root and check runtime loading:

```bash
sudo python3 check_led_status.py --d7-led
```

Expected: `PASS: D7 LED code and hooks loaded.` Then keep capture active and test HDMI loss/return. To recover, use the same write/read/compare procedure with the preserved known-good backup, followed by a power cycle. A backup taken now contains the current D7 patch, not the original image.

## HID status and a keybind example

The vendor HID command `0xB5` reads the memory address; this card exposes IRAM `0x20` through that interface. The Linux helper sends a read request using HID SET_FEATURE, reads the reply using GET_FEATURE, and checks the echoed command/address. Sending a SET_FEATURE read request is not a firmware/register write. See [amnemonic's protocol description](https://github.com/amnemonic/MacroSilicon#hid-endpoint) and the [Linux hidraw API](https://docs.kernel.org/hid/hidraw.html).

Core interpretation:

```python
flags20 = read_byte(fd, 0x20)
signal_present = not bool(flags20 & 0x10)
# GPIO LED request in the firmware:
led_on = signal_present and read_byte(fd, 0xCC03) < 128
```

The existing `hdmi_keys.py` is the full runnable example: it identifies the card, verifies D7LED01, polls every 0.2 seconds, requires one second of stable state, and sends a single numpad key per transition. Startup and USB reconnection establish a silent baseline. Read failures pause detection rather than sending a false HDMI-disconnect key. It prevents duplicate watcher instances and defaults to logging only.

The key-output portion is equivalent to:

```python
import subprocess


def emit_hdmi_key(signal_present):
    key = "KP_1" if signal_present else "KP_2"
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", "--delay", "300", key],
        check=True, timeout=5,
    )

# Call only after a debounced transition, not on every poll or initial reading.
```

This uses [xdotool](https://github.com/jordansissel/xdotool) to produce desktop X11 key events. The key press was lengthened while troubleshooting missed events. F13/F14 were tried but did not register in the user's OBS hotkey fields, even after lengthening the press. Switching to numpad 1/2 worked. The exact F13/F14 failure cause was not established.

### Setup and use

```bash
sudo apt install xdotool
sudo install -m 644 70-ms2109-hid.rules /etc/udev/rules.d/70-ms2109-hid.rules
sudo udevadm control --reload-rules
```

Reconnect the card's USB after installing the rule. Keep `hdmi_keys.py` and `check_led_status.py` together. Start OBS/VLC capture, turn Num Lock on, and run the watcher as the desktop user **without sudo**:

```bash
# Log only:
python3 hdmi_keys.py

# Generate keys:
python3 hdmi_keys.py --send-keys
```

To bind a key without changing HDMI, run one of these, then click the desired OBS hotkey field within five seconds:

```bash
python3 hdmi_keys.py --test-key KP_1
python3 hdmi_keys.py --test-key KP_2
```

Run the tests separately so there is time to choose the appropriate field. Each test sends a real key. Release modifiers before binding. Stop the watcher with Ctrl+C before stopping capture. These are the numeric keypad keys, not the number row; using those physical keypad keys can also activate the bound actions.

System-wide injection does not broadcast ordinary typing to every application. Normal events reach the focused application; background actions depend on the target application's global-hotkey handling and settings.

## What changes under Wayland?

The LED firmware and USB HID status reading are independent of X11/Wayland. The **current keyboard-output backend is X11-only**, and the script explicitly rejects key-output mode when `XDG_SESSION_TYPE=wayland`. Its log-only mode does not need X11.

xdotool's XTEST approach is not a general way to inject keys into native Wayland applications; its upstream README documents Wayland limitations. A possible future replacement is a virtual keyboard using Linux **uinput**, which creates input events through `/dev/uinput`. That requires appropriate device permissions and compositor acceptance, and application/global-shortcut behavior would still need testing. See [xdotool's Wayland status](https://github.com/jordansissel/xdotool#wayland) and [the kernel uinput documentation](https://docs.kernel.org/input/uinput.html).

No Wayland backend or virtual keyboard is included. Installing the supplied rule enables HID access only; it does not grant access to `/dev/uinput`. No autostart service is installed.

## Quick validation and troubleshooting

1. Check `sha256sum -c SHA256SUMS` from the repository root before flashing.
2. Verify the EEPROM write with a fresh readback; a successful write message is not sufficient.
3. Disconnect the programmer, boot over USB and run the D7 diagnostic. Confirm the chip ID, header, hook jumps and `D7LED01` marker before interpreting signal readings.
4. Start capture, leave USB connected and disconnect HDMI. The absent bit should become 1 and the LED request should be off.
5. Reconnect an active HDMI source. The absent bit should become 0 and the phase should progress while the LED blinks.
6. Try the watcher in log-only mode before enabling actual keys. A steady state should not repeatedly emit events.

| Symptom | Check |
| --- | --- |
| Programmer not found | Look for USB `1a86:5512`; this programming mode does not need a serial tty. |
| Two backup reads match but the header looks wrong | Confirm `-s 24c16 -c 0`, EEPROM type and wiring. Repeatability does not prove correct addressing. |
| EEPROM comparison differs | Recheck solder joints and connections; do not treat the image as verified. |
| D7 marker or hook check fails | Confirm the exact image, successful readback and a full power cycle. Do not bypass the identity checks. |
| LED blinks without HDMI while capture is closed | Known idle-status limitation; start capture before interpreting it. |
| HID permission denied | Install the rule and reconnect USB, then run the watcher as the desktop user. |
| Watcher prints “Would send” | It is in dry-run mode. Use `--send-keys` to enable key output. |
| No event at startup | Intentional silent baseline; cause a real HDMI transition after the baseline settles. |
| USB removal causes no numpad 2 | Intentional: losing the card is an unknown state, not a confirmed HDMI loss. |
| Application misses a key | Test `--test-key KP_1` in its shortcut field; enable Num Lock and verify the session is X11. |
| Wayland key output is rejected | The current backend is X11-only; see the Wayland section. |

Run the included host tests without hardware or injected key events:

```bash
python3 -m unittest test_hdmi_keys -v
```

The tests cover initial state suppression, connection/disconnection mapping, noise rejection, reconnect baseline behavior and firmware validation. Passing these tests is not a substitute for testing the actual board and target desktop application.

## Media and attribution

The repository includes only the nine supplied files in `images/`: seven still images and two GIFs, each embedded above. The photographs, annotations and recordings were supplied by proot. The product screenshot and MacroSilicon-branded pinout include third-party material; supplying or hosting them does not transfer ownership or establish a new license. No external image URLs or invented media are used in this README.

## Repositories and acknowledgements

These are the repositories used or consulted during the firmware, programmer and keybind work, with their roles distinguished:

| Repository | Role |
| --- | --- |
| [NKTKLN/ms2109-d7-1024x600](https://github.com/NKTKLN/ms2109-d7-1024x600) | D7 ROM, reverse-engineering notes and tools; D7 header/hooks/EDID reference. Local reference commit: `3e671e282850a581b3f8dd822b3545e55ef51ba5`. Its 1024×600 firmware is not the image flashed here. |
| [amnemonic/MacroSilicon](https://github.com/amnemonic/MacroSilicon) | MS2109 memory map and vendor HID read protocol, including command/address echo format. |
| [BertoldVdb/ms-tools](https://github.com/BertoldVdb/ms-tools) | MacroSilicon GPIO/firmware research, especially GPIO data and direction handling; also a dependency credited by the D7 reference project. The final physical flash used CH341A, not an assumed `msctl` operation. |
| [kraln/macrosilicon_firmware](https://github.com/kraln/macrosilicon_firmware) | Origin confirmed from the user's local original firmware checkout; earlier firmware, boot and patch architecture investigation. The first A7-based LED attempt was superseded by the successful D7 patch. |
| [command-tab/ch341eeprom](https://github.com/command-tab/ch341eeprom) | Actual Linux CH341A/24C16 flashing tool. Local commit: `7cffbef7552d93162bd90cae836a45e94acb93fb`. Its README credits original author asbokid and modifications by command-tab. |
| [jordansissel/xdotool](https://github.com/jordansissel/xdotool) | X11 synthetic key events in the host watcher; key timing and Wayland limitations. |

Build tooling: [SDCC](https://sdcc.sourceforge.net/). Programmer-tool ancestry: [asbokid's ch341eepromtool](https://sourceforge.net/projects/ch341eepromtool/). Linux API references are linked in the relevant sections above. Hardware observations and the successful numpad/LED results are from proot's tests, not claims made by these upstream projects.
