# REA — FREEYAHIKO.lua (LUNAR / @YogzzMods)

Reverse engineering statis script cheat BGMI/PUBG 4.6.1.21605 yang
diproteksi @YogzzMods. Semua analisis murni statis — payload tidak
pernah dieksekusi.

**Hasil utama:** enkripsi string bytecode berhasil dipecahkan tanpa
runtime/loader — XOR kunci 32-byte per-posisi (`xorkey32.txt`),
96,6% string terbaca penuh. Fitur terungkap: aimbot multi-modus,
wallhack, ESP, anti-bot, VIP licensing + HWID.

## Isi

| File | Keterangan |
|---|---|
| `RE_REPORT.md` | Laporan lengkap (identitas, struktur, kripto, fitur) |
| `xorkey32.txt` | Kunci 32-byte (hex) |
| `decoded_strings.json` | 4.598 string hasil dekripsi |
| `allstrings.json` | Ciphertext mentah (offset + hex) |
| `chains.json` | Peta tabel konstanta |
| `report_data.txt` | Scrining fitur |
| `tools/` | Toolchain: parser dump 5.3, scanner chain, pemecah kunci |

## Alur pemecahan (tools/)

1. `lundump.py` — parser dump Lua 5.3 (size_t=4) → bukti poison + opcode shuffle
2. `scanB.py` — scan bebas-struktur → 4.598 ciphertext
3. `cipher1..3.py` — analisis distribusi/awalan → hipotesis posisi
4. `key16fast.py` XOR period-16 awal → `fixkey*.py` anchor known-plaintext
   (`pcall`, `tostring`, watermark) → `padsolve*.py` oracle GUID-hex +
   watermark → `finaldec.py` dekripsi final

## Bonus: laporan terperinci per tahap

Laporan lengkap termasuk sisa yang belum (tabel opcode shuffle,
`game_patch_*.pak` encrypted) ada di `RE_REPORT.md`.

—

Ditambah sebagai dokumentasi metodologi analisis statis `@YogzzMods`
untuk PUBG versi 4.6.1.21605.
