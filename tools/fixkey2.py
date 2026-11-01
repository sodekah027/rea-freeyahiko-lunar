#!/usr/bin/env python3
import json

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]
key = json.load(open('xkey.json')) if False else [0x11, 0x21, 0x36, 0x47, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84, 0x90, 0xd8, 0xab, 0x00, 0x8c, 0x34]
L = 16

def dec(s, k):
    return bytes(b ^ k[i % L] for i, b in enumerate(s))

# bucket of cipher bytes per slot
bucket = [[] for _ in range(L)]
for s in strs:
    for i, b in enumerate(s):
        bucket[i % L].append(b)

hexset = set(b"0123456789abcdef")
def slot_score(j, k):
    sc = 0
    for b in bucket[j]:
        p = b ^ k
        if p in hexset: sc += 3
        elif 97 <= p <= 122: sc += 2       # lowercase letters
        elif 65 <= p <= 90: sc += 1
        elif p in b' ._-/*#%:,()[]<>"+=': sc += 1
        elif p in (10, 13): sc += 0
        else: sc -= 3
    return sc

print("per-slot best (hex-weighted):")
for j in range(L):
    scores = [(slot_score(j, k), k) for k in range(256)]
    scores.sort(reverse=True)
    cur = scores[0][1]
    mark = "  <== CHANGE" if cur != key[j] else ""
    print(f"slot {j:2d}: current={key[j]:#04x} best={cur:#04x} (2nd={scores[1][1]:#04x}){mark}")
    key[j] = cur

key = [s[1] for s in [ (max(range(256), lambda k: slot_score(j,k)), None) for j in range(L)]] if False else key

print("\nrefined:", [hex(k) for k in key])
json.dump(key, open('xkey.json', 'w'))
open('xorkey.txt', 'w').write(bytes(key).hex())

n = 0
for s in strs:
    if len(s) >= 4:
        d = dec(s, key)
        pr = sum(1 for b in d if 32 <= b < 127) / len(d)
        if pr >= 1.0 and n < 70:
            print(repr(d))
            n += 1
json.dump([dec(s, key).decode('latin1') for s in strs], open('decoded_strings.json', 'w'))
print("saved decoded_strings.json")
