#!/usr/bin/env python3
# scan file for valid Lua5.3 constant-record chains (structure-agnostic)
import struct, json, sys

data = open('FREEYAHIKO.lua','rb').read()
N = len(data)

def try_chain(off, min_records=2, max_records=100000):
    """try parse constant records starting at off; return (records, end_off) or None"""
    recs = []
    p = off
    for i in range(max_records):
        if p >= N: break
        t = data[p]; p += 1
        if t == 0: recs.append(('nil', None))
        elif t == 1:
            if p >= N: return None
            recs.append(('bool', data[p])); p += 1
        elif t == 3:
            if p+8 > N: return None
            recs.append(('float', struct.unpack_from('<d', data, p)[0])); p += 8
        elif t == 0x13:
            if p+8 > N: return None
            recs.append(('int', struct.unpack_from('<q', data, p)[0])); p += 8
        elif t in (4, 20):
            c = data[p]; p += 1
            if c == 0: return None
            c -= 1
            if c == 0xFF:
                if p+4 > N: return None
                ln = struct.unpack_from('<I', data, p)[0]; p += 4
            else:
                ln = c
            if ln <= 0 or ln > 0x10000 or p+ln > N: return None
            recs.append(('str', bytes(data[p:p+ln]))); p += ln
        else:
            if len(recs) >= 4:
                return recs, p
            return None
        if len(recs) >= 3 and len(recs) >= min_records:
            pass
    return (recs, p) if recs else None

# find candidate chain starts: every position; keep chains of >= 6 records
chains = []
off = 0
best = None
for off in range(N - 40):
    r = try_chain(off, 4)
    if r:
        recs, end = r
        if len(recs) >= 4:
            chains.append((off, end, len(recs), recs))

# merge overlapping chains (keep longest spanning each region)
merged = []
for c in sorted(chains, key=lambda x: (x[0], -(x[2]))):
    if merged and c[0] < merged[-1][1]:
        if c[2] > merged[-1][2] and c[0] >= merged[-1][0]:
            merged[-1] = c
        continue
    merged.append(list(c))

total_str = 0
strings = []
for (off, end, nrec, recs) in merged:
    strs = [r[1] for r in recs if r[0] == 'str']
    total_str += len(strs)
    strings += [(off + i, s) for i, s in enumerate(strs)]
    print(f"chain off={off} end={end} recs={nrec} strings={len(strs)} other={nrec-len(strs)}")
    for r in recs[:6]:
        if r[0] == 'str':
            print("   str:", r[1][:60])
        else:
            print("  ", r[0], r[1])
print(f"merged chains: {len(merged)}  total strings: {total_str}")
with open('chains.json','w') as f:
    json.dump([{'off':o,'end':e,'nrec':n} for (o,e,n,_) in merged], f)
with open('allstrings.json','w') as f:
    json.dump([[o, s.hex(), s.decode('latin1')] for o,s in strings], f)
print("allstrings.json written:", len(strings))
