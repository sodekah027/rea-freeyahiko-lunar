#!/usr/bin/env python3
import json, collections, math

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]

# collect byte distribution per position
maxpos = 40
dists = [collections.Counter() for _ in range(maxpos)]
for s in strs:
    for i, b in enumerate(s):
        if i < maxpos:
            dists[i][b] += 1

def cosine(a, b):
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    if not na or not nb: return 0
    return sum(a[k]*b[k] for k in a if k in b) / (na*nb)

print("position byte-distribution pairwise cosine (0..16):")
hdr = "    " + "".join(f"{j:4d}" for j in range(17))
print(hdr)
for i in range(17):
    row = f"{i:3d} "
    row += "".join(f"{cosine(dists[i], dists[j]):4.2f}" for j in range(17))
    print(row)

# hypothesis K0: cluster candidates: if many strings start 'gg.'
# look for concrete candidates: strings starting with 4e 66 (assumed "gg")
gg = [s for s in strs if len(s) >= 3 and s[0] == 0x4e and s[1] == 0x66]
print("\nn strings starting 4e66:", len(gg))
c2 = collections.Counter(s[2] for s in gg if len(s) > 2)
print("c2 dist:", [(hex(b), n) for b, n in c2.most_common(10)])
c3 = collections.Counter((s[2], s[3]) for s in gg if len(s) > 3)
print("(c2,c3) dist:", [((hex(a), hex(b)), n) for (a, b), n in c3.most_common(12)])

# also strings starting 4e 53:
gg2 = [s for s in strs if len(s) >= 4 and s[0] == 0x4e and s[1] == 0x53]
print("\nn strings starting 4e53:", len(gg2))
c2b = collections.Counter(s[2] for s in gg2 if len(s) > 2)
print("c2 dist:", [(hex(b), n) for b, n in c2b.most_common(10)])
c3b = collections.Counter((s[2], s[3], s[4]) for s in gg2 if len(s) > 4)
print("(c2,c3,c4) dist:", [((hex(a), hex(b), hex(c)), n) for (a, b, c), n in c3b.most_common(12)])
for s in gg2[:15]:
    print("   ", s.hex(), s)
