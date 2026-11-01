#!/usr/bin/env python3
import json, collections

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]

known = [0x11,0x21,0x36,0x47,0x46,0x57,0xa7,0x8d,0x9d,0x84,0x90,0xd8,0xab,0x00,0x8c,0x35]

wm_cipher = bytes.fromhex("615359332334d3e8f9a4f2a18b40d55a41608da93761cb")
wm_plain = b"protected by @YogzzMods"
wm_pad = [wm_cipher[i] ^ wm_plain[i] for i in range(23)]

hexset = set(b"0123456789abcdef")
freq = dict(zip("etaonihsrdlucmwygpbfkvjqxz",
    [12.7,9.1,8.2,7.5,7.0,6.7,6.3,6.1,6.0,4.3,4.0,2.8,2.8,2.4,2.4,2.2,2.0,1.9,1.5,1.3,0.8,0.8,0.1,0.1,0.1]))

# Pool by slot = i mod 32. Classify string as hex-oracle if first 16 decode-hex under known key0..15
def prefix_hex(s):
    d = bytes((s[i] ^ known[i]) for i in range(min(16, len(s))))
    return len(s) >= 20 and all(ch in hexset for ch in d)

L = 32
hexb = [collections.Counter() for _ in range(L)]
wordb = [collections.Counter() for _ in range(L)]
for s in strs:
    kind = "hex" if prefix_hex(s) else "word"
    for i, b in enumerate(s):
        slot = i % L
        if kind == "hex":
            hexb[slot][b] += 10
        else:
            wordb[slot][b] += 2

key32 = []
for slot in range(L):
    votes = {}
    # watermark authority for slots 0..22 (positions 0..22 of wm)
    if slot < 23:
        mm = [p for p in range(slot, 23, L)]  # only slot itself
        cand = wm_pad[slot]
    else:
        cand = None
    best = None
    for k in range(256):
        sc = 0
        for c, w in hexb[slot].items():
            sc += w if (c ^ k) in hexset else -w
        for c, w in wordb[slot].items():
            ch = c ^ k
            if 97 <= ch <= 122:
                sc += w * (freq.get(chr(ch), 0.1) + 1)
            elif 65 <= ch <= 90:
                sc += w * 1.5
            elif ch in b' ._-/*#%:,()[]<>"+=?@$&|~^':
                sc += w
            else:
                sc -= w
        if best is None or sc > best[0]:
            best = (sc, k)
    chosen = cand if cand is not None else best[1]
    if chosen != best[1] and cand is not None:
        print(f"slot {slot}: watermark authority {cand:#x} (oracle said {best[1]:#x})")
    key32.append(chosen)

print("key32:", [hex(k) for k in key32])
print("key32 bytes:", bytes(key32))
open('xorkey32.txt', 'w').write(bytes(key32).hex())

def dec(s):
    return bytes(b ^ key32[i % L] for i, b in enumerate(s))

ok = bad = 0
badl = []
for s in strs:
    d = dec(s)
    pr = sum(1 for b in d if 32 <= b < 127 or b in (10, 13, 9)) / max(1, len(d))
    if pr >= 0.95: ok += 1
    else: bad += 1; badl.append(d)
print(f"clean: {ok}/{len(strs)}  bad: {bad}")

json.dump([dec(s).decode('latin1') for s in strs], open('decoded_strings.json', 'w'))
print("saved decoded_strings.json")

# dump 60 random interesting decodes
import re
shown = 0
for s in strs:
    d = dec(s)
    if len(d) >= 12 and re.match(rb'^[\x20-\x7e]+$', d):
        print(d.decode())
        shown += 1
        if shown > 60: break
