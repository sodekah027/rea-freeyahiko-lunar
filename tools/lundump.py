#!/usr/bin/env python3
# Lua 5.3 lundump parser (32-bit build: int=4, size_t=4"
import sys, struct, json

data = open(sys.argv[1], 'rb').read()
pos = 0

def u8():
    global pos
    v = data[pos]; pos += 1; return v
def i32():
    global pos
    v = struct.unpack_from('<i', data, pos)[0]; pos += 4; return v
def i64():
    global pos
    v = struct.unpack_from('<q', data, pos)[0]; pos += 8; return v
def f64():
    global pos
    v = struct.unpack_from('<d', data, pos)[0]; pos += 8; return v
def string():
    global pos
    c = u8()
    if c == 0: return None
    c -= 1
    if c == 0xFF:
        n = i32()
    else:
        n = c
    s = data[pos:pos+n]; pos += n
    return s

# header
assert data[:4] == b'\x1bLua'
version = data[4]; fmt = data[5]
sizes = data[13], data[12], data[14], data[15], data[16]
int_sz, sizet_sz, instr_sz, int64_sz, num_sz = sizes
pos = 17
assert i64() == 0x5678, "LUAC_INT mismatch"
assert abs(f64() - 370.5) < 1e-9, "LUAC_NUM mismatch"

OPNAMES = ["MOVE","LOADK","LOADKX","LOADBOOL","LOADNIL","GETUPVAL","GETTABUP","GETTABLE",
"SETTABUP","SETUPVAL","SETTABLE","NEWTABLE","SELF","ADD","SUB","MUL","MOD","POW","DIV","IDIV",
"BAND","BOR","BXOR","BNOT","SHL","SHR","UNM","NOT","LEN","CONCAT","JMP","EQ","LT","LE","TEST",
"TESTSET","CALL","TAILCALL","RETURN","FORLOOP","FORPREP","TFORCALL","SETLIST","CLOSURE",
"VARARG","EXTRAARG"]
# operand modes o: ABC=0,ABx=1,AsBx=2,Ax=3,isT=4 (jump targets: AsBx/isT)
MODE = [0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,4,0,4,0,0,0,4,4,0,0,1,0,0]
sBx_bias = 2**17 - 1

def decode_instr(w):
    op = w & 0x3F
    A = (w >> 6) & 0xFF
    C = (w >> 14) & 0x1FF
    B = (w >> 23) & 0x1FF
    Bx = (w >> 14) & 0x3FFFF
    x = w >> 6
    sBx = Bx - sBx_bias
    return op, A, B, C, Bx, sBx

stats = {"protos": 0, "consts": {}, "strings": [], "n_instr": 0, "op_hist": {}}

def load_function(depth):
    global pos
    start = pos
    src = string()
    lined = i32(); linelast = i32()
    numparams = u8(); vararg = u8(); maxstack = u8()
    ncode = i32()
    code = []
    bad_ops = []
    for j in range(ncode):
        w = struct.unpack_from('<I', data, pos)[0]; pos += 4
        op, A, B, C, Bx, sBx = decode_instr(w)
        code.append((w, op, A, B, C, Bx, sBx))
        if op >= len(OPNAMES):
            bad_ops.append((j, hex(w)))
    ncon = i32()
    consts = []
    for j in range(ncon):
        t = u8()
        if t == 0: v = None; kind='nil'
        elif t == 1: v = u8(); kind='bool'
        elif t == 3: v = f64(); kind='float'
        elif t == 19: v = i64(); kind='int'
        elif t in (4, 20):
            v = string(); kind='string'
            if v is not None:
                stats["strings"].append(v)
        else:
            consts.append(('BADTAG', t, pos)); 
            print(f"BAD CONST TAG {t:#x} at offset {pos-1} proto depth {depth} #const {j}")
            code_off = start + 1 + 8 + 3 - (1 if src is None else 0) + (0 if src is None else len(src))
            print(f"  fail-context: proto_start={start} ncode={ncode} nconst={ncon} numparams={numparams} vararg={vararg} maxstack={maxstack} srclen={len(src) if src else 0} code_end={start+11+4*ncode-(0 if src is None else len(src))}")
            return None
        consts.append((kind, v))
    nup = i32()
    ups = []
    for j in range(nup):
        instack = u8(); idx = u8()
        ups.append((instack, idx))
    nproto = i32()
    protos = []
    for j in range(nproto):
        print(f"{'  '*depth}  child idx={j} start={pos} parent_code={ncode}")
        p = load_function(depth+1)
        if p is None: return None
        protos.append(p)
    if pos < len(data):
        nlineinfo = i32()
        pos += 4 * nlineinfo  # 32-bit int per instruction
        nlocvars = i32()
        for j in range(nlocvars):
            string(); i32(); i32()
        nupvalnames = i32()
        for j in range(nupvalnames):
            string()
    stats["protos"] += 1
    stats["n_instr"] += ncode
    for (w, op, *_) in code:
        stats["op_hist"][op] = stats["op_hist"].get(op, 0) + 1
    dbg = locals().get('nlineinfo'), locals().get('nlocvars'), locals().get('nupvalnames')
    print(f"{'  '*depth}proto done depth={depth} ncode={ncode} nconst={ncon} nup={nup} nproto={nproto} dbg={dbg} end={pos}")
    return dict(src=src, lined=lined, linelast=linelast, numparams=numparams,
                vararg=vararg, maxstack=maxstack, code=code, consts=consts,
                ups=ups, protos=protos, bad_ops=bad_ops, path=None)

def check_jumps(f, name):
    issues = []
    for j, (w, op, A, B, C, Bx, sBx) in enumerate(f["code"]):
        nm = OPNAMES[op] if op < len(OPNAMES) else f"OP{op}?"
        if nm in ("JMP",):
            tgt = j + 1 + sBx
            if not (0 <= tgt <= len(f["code"])):
                issues.append((name, j, nm, "OOB jump " + str(tgt)))
        elif nm in ("FORLOOP","FORPREP","TFORCALL"):
            pass  # layout varies; accept
        # reuse common sense checks
        if nm in ("RETURN",) and j != len(f["code"]) - 1:
            issues.append((name, j, nm, "RETURN before last instr"))
    return issues

def walk(f, path="<main>"):
    res = []
    name = path
    res += check_jumps(f, name)
    for i, p in enumerate(f["protos"]):
        res += walk(p, f"{path}<{i}>")
    return res

nup_main = u8()
mainp = load_function(0)
if mainp is None:
    print("PARSE FAILED — print structure dump around")
    sys.exit(1)
extra = data[pos:]
jmp_issues = walk(mainp)
print(f"version={version:#x} sizes(int,sizet,instr,integer,number)={sizes}")
print(f"parsed bytes: {pos}/{len(data)}  leftover={len(extra)}")
print(f"protos={stats['protos']} instrs={stats['n_instr']} strings={len(stats['strings'])}")
bad_total = sum(len(p['bad_ops']) for p in [mainp] )
def cnt_bad(f):
    n = len(f['bad_ops'])
    for p in f['protos']: n += cnt_bad(p)
    return n
print(f"bad opcodes(>=0x2D): {cnt_bad(mainp)}")
print("jump/return anomalies:", len(jmp_issues))
for name, j, nm, why in jmp_issues[:8]:
    print("  ", name, j, nm, why)
top = sorted(stats["op_hist"].items(), key=lambda x: -x[1])[:12]
print("opcode histogram (top12):", [(OPNAMES[o] if o < len(OPNAMES) else f"OP{o}", c) for o, c in top])
json.dump({"op_hist": {str(k): v for k, v in stats["op_hist"].items()}}, open("ophist.json", "w"))
with open("strings.json", "w") as fh:
    json.dump([s.decode('latin1') for s in stats["strings"]], fh, indent=0)
print("strings written to strings.json")
