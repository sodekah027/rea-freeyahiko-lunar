#!/usr/bin/env python3
import json, collections

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]
pad = json.load(open('pad.json'))
pad = {int(k): v for k, v in pad.items()}
for p in [16, 17, 18, 19, 20, 21, 22]:
    cm = bytes.fromhex("615359332334d3e8f9a4f2a18b40d55a41608da93761cb")
    wm = b"protected by @YogzzMods"
    pad[p] = cm[p] ^ wm[p]   # keep watermark exact

hexset = set(b"0123456789abcdef")
freq = dict(zip("etaonihsrdlucmwygpbfkvjqxz",
    [12.7,9.1,8.2,7.5,7.0,6.7,6.3,6.1,6.0,4.3,4.0,2.8,2.8,2.4,2.4,2.2,2.0,1.9,1.5,1.3,0.8,0.8,0.1,0.1,0.1]))

def dec(s, pad):
    return bytes(b ^ pad[i] for i, b in enumerate(s))

# classify strings by verified prefix (0..15) type
def prefix_kind(s):
    d = dec(s, pad)
    p16 = d[:16]
    if all(ch in hexset for ch in p16) and len(s) >= 20:
        return "hex"
    return "word"

MAXP = max(len(s) for s in strs)
print("solving positions 23..", MAXP)
for p in range(23, MAXP):
    hexb = collections.Counter()
    wordb = collections.Counter()
    for s in strs:
        if len(s) <= p:
            continue
        if prefix_kind(s) == "hex":
            hexb[s[p]] += 10
        else:
            wordb[s[p]] += 2
    if not hexb and not wordb:
        break
    best = None
    for k in range(256):
        sc = 0
        for c, w in hexb.items():
            if (c ^ k) in hexset:
                sc += w
            else:
                sc -= w
        for c, w in wordb.items():
            ch = c ^ k
            if 97 <= ch <= 122:
                sc += w * (freq.get(chr(ch), 0.1) + 1)
            elif 65 <= ch <= 90:
                sc += w * 1.5
            elif ch in b' ._-/*#%:,()[]<>"+=?':
                sc += w
            else:
                sc -= w
        if best is None or sc > best[0]:
            best = (sc, k)
    pad[p] = best[1]

print("pad 23..45:", [hex(pad[p]) for p in range(23, 46)])
print("\n=== long strings after oracle solve ===")
shown = 0
for s in strs:
    if len(s) > 18:
        d = dec(s, pad)
        pr = sum(1 for b in d if 32 <= b < 127) / len(d)
        if pr >= 0.99 and shown < 50:
            print(len(s), repr(d))
            shown += 1
json.dump({str(k): v for k, v in pad.items()}, open('pad.json', 'w'))
json.dump([dec(s, pad).decode('latin1') for s in strs], open('decoded_strings.json', 'w'))
print("saved")
