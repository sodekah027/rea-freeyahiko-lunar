#!/usr/bin/env python3
# Fast inventory: find all valid Lua5.3 constant chains via single sliding pass with restart
import struct, json

data = open('FREEYAHIKO.lua','rb').read()
N = len(data)

def rec_at(p):
    """parse one constant record at p; return (kind, value, newp) or None"""
    if p >= N: return None
    t = data[p]; p += 1
    if t == 0: return ('nil', None, p)
    if t == 1:
        if p >= N: return None
        return ('bool', data[p], p+1)
    if t == 3:
        if p+8 > N: return None
        return ('float', struct.unpack_from('<d',data,p)[0], p+8)
    if t == 0x13:
        if p+8 > N: return None
        return ('int', struct.unpack_from('<q',data,p)[0], p+8)
    if t in (4, 20):
        if p >= N: return None
        c = data[p]-1; p += 1
        if c == 0xFF:
            if p+4 > N: return None
            ln = struct.unpack_from('<I',data,p)[0]; p += 4
        else:
            if c < 0: return None
            ln = c
        if ln <= 0 or ln > 0x4000 or p+ln > N: return None
        return ('str', bytes(data[p:p+ln]), p+ln)
    return None

# multi-seed approach: try to start a chain at every offset; extend; keep chains >= 5 records
# but jump ahead past a found chain to avoid quadratic blowup
found = []
off = 0
p = 0
runs = []
try:
    cur_start = None
    cur_recs = []
    while p < N-1:
        r = rec_at(p)
        if r is None:
            if len(cur_recs) >= 5:
                runs.append((cur_start, p, cur_recs))
            cur_start = None; cur_recs = []
            p += 1
        else:
            if cur_start is None:
                cur_start = p
                cur_recs = []
            cur_recs.append(r)
            p = r[2]
    if len(cur_recs) >= 5:
        runs.append((cur_start, p, cur_recs))
except Exception as e:
    print("ERR", e); raise

# collapse overlapping runs: greedy by length
runs.sort(key=lambda x: (x[0], -(len(x[2]))))
picked = []
for r in runs:
    s, e, recs = r
    if picked and s < picked[-1][1]:
        # overlaps: keep the one with more strings
        if recs and len(recs) >= len(picked[-1][2]):
            picked[-1] = r
        continue
    picked.append(r)

strings_all = []
out = []
for (s, e, recs) in picked:
    strs = [(s+i, x[1]) for i, x in enumerate(recs) if x[0] == 'str']
    others = [x for x in recs if x[0] != 'str']
    out.append({'off': s, 'end': e, 'nrec': len(recs), 'nstr': len(strs)})
    strings_all += strs
    print(f"chain {s}..{e} recs={len(recs)} strs={len(strs)} nonstr={len(others)}")
json.dump(out, open('chains.json','w'))
json.dump([[o, s.hex(), s.decode('latin1')] for o, s in strings_all], open('allstrings.json','w'))
print("TOTAL strings:", len(strings_all))
print("chairs:", len(picked))
