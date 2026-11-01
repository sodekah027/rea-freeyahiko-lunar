#!/usr/bin/env python3
# Solve per-position pad (not modular) using pure-hex verified strings as oracle
import json, collections, re

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]
key16 = [0x11, 0x21, 0x36, 0x47, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84, 0x90, 0xd8, 0xab, 0x00, 0x8c, 0x35]

def dec16(s):
    return bytes(b ^ key16[i % 16] for i, b in enumerate(s))

# stage 1: classify strings that decode to pure hex under the 16-key (len>=6)
hexres = re.compile(rb'^[0-9a-f]+$')
wordres = re.compile(rb'^[A-Za-z0-9_ .\-/*#:<>%()"\'+=\[\]{}!?@$&|~^,;`]*$')
hexstrs = [s for s in strs if len(s) >= 6 and hexres.match(dec16(s) if len(s) <= 16 else dec16(s))]
print("hex-verified pure strings:", len(hexstrs))

hexset = set(b"0123456789abcdef")
letters = set(range(97, 123)) | set(range(65, 91))

# For each ABSOLUTE position p (0..99): bucket of cipher bytes at that position
# weighted: hex-string bytes weight 3, other clean-word bytes weight 1
MAXP = 100
pad = {}
for p in range(MAXP):
    cnt = collections.Counter()
    for s in hexstrs:
        if len(s) > p:
            cnt[s[p]] += 3
    # other clean short strings contribute letter-frequency score
    for s in strs:
        if len(s) > p:
            d = dec16(s)
            # only strings fully convincing under known key start (prefix ok to p)
            if len(s) <= 16 or p >= 16:
                cnt[s[p]] += 0  # skip ambiguity
    if not cnt:
        continue
    # solve k: maximize sum w*score(c^k) where score favors hex chars
    best = None
    for k in range(256):
        sc = 0
        for c, w in cnt.items():
            pch = c ^ k
            if pch in hexset:
                sc += w
            elif pch in letters:
                sc += w * 0.2
        if best is None or sc > best[0]:
            best = (sc, k)
    pad[p] = best[1]

# merge: 0..15 = validated key16; 16.. = from hex oracle
for p in range(16):
    pad[p] = key16[p]
print("solved pad positions:", len(pad))
print("pad[0..40]:", [hex(pad[p]) for p in range(min(41, len(pad)))])
print("pad bytes 0-47 as str:", bytes(pad[p] for p in range(48)))

# verify: decode long strings
def decfull(s):
    return bytes(b ^ pad[i] for i, b in enumerate(s))

print("\n=== long strings decoded ===")
shown = 0
for s in strs:
    if len(s) > 18:
        d = decfull(s)
        pr = sum(1 for b in d if 32 <= b < 127) / len(d)
        if pr > 0.95 and shown < 40:
            print(repr(d))
            shown += 1
json.dump({str(k): v for k, v in pad.items()}, open('pad.json', 'w'))
print("\nsaved pad.json")
