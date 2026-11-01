#!/usr/bin/env python3
# Extend pad: p16..22 from watermark; beyond via per-position letter/hex scoring
import json, collections

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]
key16 = [0x11, 0x21, 0x36, 0x47, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84, 0x90, 0xd8, 0xab, 0x00, 0x8c, 0x35]
pad = {p: key16[p] for p in range(16)}

# watermark oracle
wm_cipher = bytes.fromhex("615359332334d3e8f9a4f2a18b40d55a41608da93761cb")
wm_plain = b"protected by @YogzzMods"
assert len(wm_cipher) == len(wm_plain), (len(wm_cipher), len(wm_plain))
for i in range(len(wm_plain)):
    pad[i] = wm_cipher[i] ^ wm_plain[i]
print("pad 0..22 set")

freq = dict(zip("etaonihsrdlucmwygpbfkvjqxz",
    [12.7,9.1,8.2,7.5,7.0,6.7,6.3,6.1,6.0,4.3,4.0,2.8,2.8,2.4,2.4,2.2,2.0,1.9,1.5,1.3,0.8,0.8,0.1,0.1,0.1]))
hexset = set(b"0123456789abcdef")

def score_byte(pch, p=None):
    if pch in hexset: return 3
    if 97 <= pch <= 122: return freq.get(chr(pch), 0.2) + 18
    if 65 <= pch <= 90: return freq.get(chr(pch+32), 0.2) * 0.7 + 8
    if 48 <= pch <= 57: return 5
    if pch in b' ._-/*#%:,()[]<>"+=?~_': return 6
    if pch in (10, 13): return 2
    return -25

MAXP = max(len(s) for s in strs)
print("longest string:", MAXP)
for p in range(16, MAXP):
    cnt = collections.Counter()
    for s in strs:
        if len(s) > p:
            cnt[s[p]] += 1
    if not cnt:
        break
    best = None
    for k in range(256):
        sc = sum(w * score_byte(c ^ k) for c, w in cnt.items())
        if best is None or sc > best[0]:
            best = (sc, k)
    pad[p] = best[1]
    # sanity check against watermark if covered
    if p < len(wm_plain) and pad[p] != wm_cipher[p] ^ wm_plain[p]:
        print(f"WARN pos {p}: score said {pad[p]:#x}, watermark says {(wm_cipher[p]^wm_plain[p]):#x} -> using watermark")
        pad[p] = wm_cipher[p] ^ wm_plain[p]

def decfull(s):
    return bytes(b ^ pad[i] for i, b in enumerate(s))

print("pad 0..40:", [hex(pad[p]) for p in range(41)])
print("\n=== long strings check ===")
shown = 0
for s in strs:
    if len(s) > 16:
        d = decfull(s)
        pr = sum(1 for b in d if 32 <= b < 127) / len(d)
        if pr >= 0.99 and shown < 50:
            print(len(s), repr(d))
            shown += 1
json.dump({str(k): v for k, v in pad.items()}, open('pad.json', 'w'))
json.dump([decfull(s).decode('latin1') for s in strs], open('decoded_strings.json', 'w'))
print("saved pad.json + decoded_strings.json")
