#!/usr/bin/env python3
import json, re, collections

st = json.load(open('allstrings.json'))
strs = [bytes.fromhex(h) for _, h, _ in st]
key = [0x11, 0x21, 0x36, 0x47, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84, 0x90, 0xd8, 0xab, 0x00, 0x8c, 0x35]
L = 16
def dec(s):
    return bytes(b ^ key[i % L] for i, b in enumerate(s))

# find watermark candidate: should decode to something like "-- protected by @YogzzMods"
for s in strs:
    d = dec(s)
    if b"rotected by @" in d:
        print("watermark raw:", s.hex(), "->", d)

# overall printable stats
ok = bad = 0
decoded = []
for s in strs:
    d = dec(s)
    decoded.append(d)
    pr = sum(1 for b in d if 32 <= b < 127 or b in (10, 13, 9)) / max(1, len(d))
    if pr >= 0.95: ok += 1
    else: bad += 1
print(f"fully-printable-ish strings: {ok}/{len(strs)}  bad: {bad}")

# feature keyword scan
keywords = [b"aimbot", b"Aimbot", b"esp", b"Esp", b"ESP", b"color", b"Color", b"menu", b"Menu", b"bone",
    b"Bone", b"track", b"Track", b"speed", b"Speed", b"teleport", b"Tele", b"Fly", b"fly", b"gloo",
    b"Gloo", b"wall", b"Wall", b"hack", b"Hack", b"hack_", b"virt", b"Virt", b"sensor", b"Sensor",
    b"silent", b"Silent", b"magic", b"Magic", b"bullet", b"Bullet", b"fire", b"Fire", b"big", b"Big",
    b"head", b"Head", b"view", b"View", b"hook", b"Hook", b"offset", b"Offset", b"value", b"Value",
    b"guest", b"Guest", b"room", b"Room", b"title", b"Title", b"author", b"Author", b"update", b"Update",
    b"log", b"Logo", b"gg.", b"toast", b"alert", b"prompt"]
hits = collections.Counter()
interesting = []
for d in decoded:
    for kw in keywords:
        if kw in d:
            hits[kw] += 1
            interesting.append(d)
            break
print("\nkeyword hit counts:", hits.most_common(30))
print("\n=== sample interesting strings ===")
seen = set()
n = 0
for d in interesting:
    t = d.decode('latin1')
    if t not in seen:
        seen.add(t)
        print(t[:90])
        n += 1
    if n > 60: break

json.dump([d.decode('latin1') for d in decoded], open('decoded_strings.json', 'w'))
print("\nsaved decoded_strings.json")
