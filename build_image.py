from pathlib import Path
import hashlib
code=Path('firmware.bin').read_bytes();assert len(code)==512
# Reference D7 header configuration; no donor executable firmware imported.
b=bytearray([255]*2048)
b[:16]=bytes.fromhex('5aa502000910ffffffffffff18090611')
b[48:48+len(code)]=code;end=48+len(code)
b[end:end+2]=(sum(b[2:48])&65535).to_bytes(2,'big')
b[end+2:end+4]=(sum(code)&65535).to_bytes(2,'big')
assert b[4]==9 and b[5]==16
assert all(sum(code[i:i+128])%256==0 for i in (256,384))
name='ms2109_d7_led_v1.bin';Path(name).write_bytes(b)
print(name,len(b),hashlib.sha256(b).hexdigest())
