#!/usr/bin/env python3
# Refine the 16-byte XOR key with known-plaintext anchors
import json

st = json.load(open('allstrings.json'))
items = [(o, bytes.fromhex(h)) for o, h, _ in st]
strs = [s for _, s in items]
L = 16

K0 = [0x27, 0x21, 0x36, 0x47, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84, 0x90, 0xdf, 0xab, 0x0, 0x8c, 0x34]

def decode(s, key):
    return bytes(b ^ key[i % L] for i, b in enumerate(s))

def find_cipher(plains):
    """find cipher string(s) that best decode to given plaintext under unknown key"""
    out = []
    for s in strs:
        if len(s) < len(plains[0]):
            continue
        for p in plains:
            if len(p) != len(s):
                continue
            # count matching positions under CURRENT key
            d = decode(s, K0)
            m = sum(1 for a, b in zip(d, p) if a == b)
            if m >= len(p) - 3:
                out.append((s, p, m))
    return out

# candidate anchors: things certainly in this corpus
anchor_plains = []
for name in ["tostring","string","error","pcall","xpcall","tonumber","math","table","ipairs","pairs",
             "require","print","loadstring","setmetatable","getmetatable","rawget","rawset",
             "collectgarbage","gcinfo","unpack","select","type","assert","visible","pos",
             "0123456789abcdef","@YogzzMods","protected by @YogzzMods",
             "horizontal","vertical","Targetbone","aimbot","esp","espon","Aimbot","AimLock","teleport",
             "invisible","Aimlock","bullettrack","TrackBullet","FlyVehicle","ColorPreview"]:
    anchor_plains.append(name.encode())

# derive slot constraints
slots = {j: {} for j in range(16)}
for p in anchor_plains:
    for s in strs:
        if len(s) != len(p):
            continue
        d = decode(s, K0)
        matches = sum(1 for a, b in zip(d, p) if a == b)
        if matches >= len(p) - 2:
            for i in range(len(s)):
                k = s[i] ^ p[i]
                slots[i % 16][k] = slots[i % 16].get(k, 0) + 1
            print(f"anchor hit: plain={p!r} matches={matches}/{len(p)}")

key = list(K0)
for j in range(16):
    if slots[j]:
        best_k, votes = max(slots[j].items(), key=lambda kv: kv[1])
        if votes >= 2:
            if best_k != key[j]:
                print(f"slot {j}: {key[j]:#x} -> {best_k:#x} (votes={votes})")
                key[j] = best_k
            else:
                print(f"slot {j}: confirm {best_k:#x}")

print("\nREFINED KEY:", [hex(k) for k in key])
print("as bytes:", bytes(key))
with open('xorkey.txt', 'w') as f:
    f.write(bytes(key).hex())

def dec2(s):
    return bytes(b ^ key[i % 16] for i, b in enumerate(s))
print("\n=== SAMPLES ===")
shown = 0
for s in strs:
    if len(s) >= 5:
        d = dec2(s)
        printable = sum(1 for b in d if 32 <= b < 127 or b in (10, 13, 9)) / len(d)
        if printable > 0.9 and shown < 60:
            print(repr(d))
            shown += 1

json.dump([dec2(s).decode('latin1') for s in strs], open('decoded_strings.json', 'w'))
print("\nsaved decoded_strings.json")

