#!/usr/bin/env python3
import json, collections

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]

# 1. conditional distributions: given pos0 byte, what pos1..3 look like
by0 = collections.defaultdict(list)
for s in strs:
    if len(s) >= 1:
        by0[s[0]].append(s)
print("cluster sizes top:", sorted(((len(v), hex(k)) for k, v in by0.items()), reverse=True)[:10])
for top in sorted(by0, key=lambda k: -len(by0[k]))[:6]:
    grp = by0[top]
    print(f"\n== cluster c0={hex(top)} n={len(grp)}")
    d1 = collections.Counter(s[1] for s in grp if len(s) > 1)
    d2 = collections.Counter(s[2] for s in grp if len(s) > 2)
    d3 = collections.Counter(s[3] for s in grp if len(s) > 3)
    print("  c1 top:", [(hex(b), c) for b, c in d1.most_common(6)])
    print("  c2 top:", [(hex(b), c) for b, c in d2.most_common(6)])
    print("  c3 top:", [(hex(b), c) for b, c in d3.most_common(6)])
    ex = grp[:12]
    for s in ex:
        print("   ", s.hex(), s)

# 2. if prefix "gg." cipher is C1C2C3 found by structure: look at overall position-0 popularity
p0 = collections.Counter(s[0] for s in strs)
print("\nposition0 global:", [(hex(b), c) for b, c in p0.most_common(12)])

# 3. repeated strings stats: how many exact duplicates
dup = collections.Counter(s for s in strs)
reps = [(s, c) for s, c in dup.items() if c > 1]
print("distinct:", len(dup), "repeated values:", len(reps), "max rep:", max(c for _, c in dup.items()))
for s, c in sorted(reps, key=lambda x: -x[1])[:10]:
    print("  rep", c, s.hex())
