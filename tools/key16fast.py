#!/usr/bin/env python3
# Fast: scoring separable per key position -> exact argmax per bucket, no iteration
import json

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]
L = 16

freq = dict(zip("etaonihsrdlucmwygpbfkvjqxz",
    [12.7,9.1,8.2,7.5,7.0,6.7,6.3,6.1,6.0,4.3,4.0,2.8,2.8,2.4,2.4,2.2,2.0,1.9,1.5,1.3,0.8,0.8,0.1,0.1,0.1]))

def score_char(p):
    if p == 0: return 30
    if 97 <= p <= 122: return freq.get(chr(p), 0.2) * 3 + 20
    if 65 <= p <= 90: return freq.get(chr(p+32), 0.2) * 1.5 + 10
    if 48 <= p <= 57: return 8
    if p in b' ._-/*#%:,()[]<>"\'!?+~=': return 12
    if p in (10, 13): return 5
    if 128 <= p <= 255: return -80
    return -40

# bucket[j][b] = count of cipher byte b at key-position j
bucket = [[0]*256 for _ in range(L)]
for s in strs:
    for i, b in enumerate(s):
        bucket[i % L][b] += 1

key = []
for j in range(L):
    best_k = 0
    for k in range(256):
        sc = sum(c * score_char(b ^ k) for b, c in enumerate(bucket[j]) if c)
        if k == 0 or sc > best_sc:
            best_sc, best_k = sc, k
    key.append(best_k)
print("key:", [hex(k) for k in key])
print("key str:", bytes(key))

def decode(s): return bytes(b ^ key[i % L] for i, b in enumerate(s))

n = 0
for s in strs:
    if len(s) >= 5:
        d = decode(s)
        if n < 50:
            print(repr(d))
        n += 1
print("total len>=5:", n)

# save all decoded
with open('decoded_strings.json','w') as f:
    json.dump([decode(s).decode('latin1') for s in strs], f)
print("saved decoded_strings.json")
