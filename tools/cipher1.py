#!/usr/bin/env python3
import json, collections

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]
print("n =", len(strs))
print("len hist:", sorted(collections.Counter(len(s) for s in strs).items())[:20])

def printable(s):
    return sum(1 for b in s if 32 <= b < 127 or b in (10, 13, 9)) / max(1, len(s))

# overall byte stats
cnt = collections.Counter()
for s in strs:
    cnt.update(s)
print("top bytes:", cnt.most_common(12))

# candidate transform score = mean printable ratio over strings len>=6
long_strs = [s for s in strs if len(s) >= 6]
print("strings len>=6:", len(long_strs))

def score_report(name, fn):
    scores = [printable(fn(s)) for s in long_strs]
    mean = sum(scores) / len(scores)
    best_idx = sorted(range(len(scores)), key=lambda i: -scores[i])[:5]
    if mean > 0.85:
        print(f"*** {name}: mean={mean:.3f}")
        for i in best_idx[:3]:
            print("     ", fn(long_strs[i])[:60])
    return mean

results = []
for k in range(1, 256):
    mean_xor = score_report(None, lambda s, k=k: bytes(b ^ k for b in s))
    mean_add = score_report(None, lambda s, k=k: bytes((b + k) & 0xFF for b in s))
    results.append((max(mean_xor, mean_add), k))
print("best xor/add k:", sorted(results, reverse=True)[:5])

# rolling xor: c[i] ^ (i & 0xFF); c[i] ^ ((i*k)&0xFF); c[i] ^ k ^ i; etc
def mk(pat):
    return lambda s: bytes(pat(i, b) for i, b in enumerate(s))

tests = {
    "xor_i":      mk(lambda i, b: b ^ (i & 0xFF)),
    "xor_add_k_i":mk(lambda i, b: (b + i) & 0xFF),
    "sub_i":      mk(lambda i, b: (b - i) & 0xFF),
    "xor_2i":     mk(lambda i, b: b ^ ((2 * i) & 0xFF)),
    "xor_seed0":  mk(lambda i, b: b ^ ((0x2f + i) & 0xFF)),
    "rev":        lambda s: s[::-1],
    "not":        lambda s: bytes((~b) & 0xFF for b in s),
}
for name, fn in tests.items():
    scores = [printable(fn(s)) for s in long_strs]
    print(f"{name}: mean={sum(scores)/len(scores):.3f} max={max(scores):.2f}")

# per-first-byte distribution
first = collections.Counter(s[0] for s in strs)
print("first-byte top:", first.most_common(15))
last = collections.Counter(s[-1] for s in strs)
print("last-byte top:", last.most_common(15))
