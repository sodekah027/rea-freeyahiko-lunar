# Laporan Reverse Engineering — FREEYAHIKO.lua

**Tanggal:** 2026-11-01 · **Metode:** statis murni (tidak ada eksekusi payload)

## 1. Identitas File

| Aspek | Hasil |
|---|---|
| File | `/storage/emulated/0/MT2/mcp/FREEYAHIKO.lua` (449.256 byte) |
| Jenis | Bytecode **custom Lua 5.3-like VM** (build 32-bit: int=4, size_t=4, instr=4, i64=8, num=8) |
| Tujuan | **Cheat PUBG Mobile / BGMI versi 4.6.1.21605** |
| Nama menu | **LUNAR** mod menu (`LunarFeatures`, `LunarESPEvents`, `LunarLoginRuntime`) |
| Protektor | **@YogzzMods** (watermark: `protected by @YogzzMods`, tanda tangan di akhir file: `\n\n-- protected by @YogzzMods\n`) |
| Pendamping | `game_patch_4.6.1.21605.pak` (2.769.213 byte, terenkripsi full, tanpa header) |
| Sumber publik | GitHub `Yogzz011/yogzzmods-lua_tool` (installer biner arm64), channel Telegram `@yogzzmods` |

## 2. Struktur Proteksi (temuan)

1. **Header dump Lua 5.3 valid** (LUAC_INT/LUAC_NUM lolos verifikasi) — menipu `luac -l` (gagal: `size_t size mismatch`, VM asli 32-bit; unluac crash `IllegalStateException` di konstanta).
2. **Proteksi ditingkatkan**: node "poison" (header proto palsu di offset 31655: numparams=32/maxstack=0) → crash parser standar.
3. **Opcode shuffle**: instruksi pertama fungsi utama `BNOT` (opcode 23, mustahil); main & child0 keduanya diakhiri word `da XX 00 64` (opcode 0x1a, bukan RETURN standar 0x26) → numbering opcode custom.
4. **Enkripsi string**: XOR kunci 32-byte per-posisi (cycle penuh, restart tiap string), kunci dipecahkan (lihat §3).
5. **Antarmuka dgn sistem asli**: string bIsABot, bIsWeaponAiming, FLinearColor, Viewport → cheat menyentuh ** Unreal Engine 4** internal (drawing ESP via UMG/Canvas).

## 3. Enkripsi String — SOLVED

Format: `plaintext[i] = ciphertext[i] XOR key32[i mod 32]`, keystream restart per konstanta string. Identik plaintext → identik ciphertext (bukti deterministik; `gg`... ok "gg" tak terlihat, tapi `pcall`/`tostring`/`string` muncul 20-30× identik).

**Kunci (hex):**
```
11 21 36 47 46 57 a7 8d 9d 84 90 d8 ab 00 8c 35
26 1a f7 e4 58 05 b8 b3 15 07 d0 2c 1e 8f f6 c8
```

Metode pemecahan:
- Anchor known-plaintext: `pcall`, `tostring`, `string`, `error` → kunci slot 0-15
- Oracle watermark: `protected by @YogzzMods` (23 byte, pasti) → kunci slot 16-22
- Oracle charset: string GUID-hex murni (`380352a5b407...` x banyak) → menyelesaikan slot 23-31
- Temuan period-32: byte posisi 32+ `=` = cycle ulang key awal.

**Hasil:** 4.442/4.598 string (96,6%) terdekrip penuh. 156 sisanya = blob panjang (>100 byte) dengan obfuscasi layer-2, dipakai sebagai paket data (asset/UI template), bukan teks.

## 4. Isi Script — Fitur Terdekripsi

### Aimbot (rekomendasi paramter lengkap)
`AimEnabled`, `AimSpeed`, `SetAimMode`, `IsAimNormal`, `AimTarget`, `SetAimTarget`, `GetAimData`, `GetBoneIndex/BoneLocation/BonePos`, per-modus:
- **Hipfire**: `AimTouchHip*` (Bone, Cond, Dist, FOV, IgBot, IgKnock, Prio, Speed, VisCheck)
- **Shotgun (SG)**: `AimTouchSG*` (+AutoFire)
- **Red dot/Scope**: `AimTouchScope*` (+ScopeAll, ScopeSniper)
- **Sniper**: `AimTouchSniper*` (+Pred = prediksi gerak)
- **Mortar**: `AimTouchMortar*` (+Pred)
- Batal visibilitas (`VisCheck`), prioritas, ignore bot/knocked
- `EspFovCircle` (lingkaran FOV di layar), `FieldOfView`

### Wallhack
`StartWallhack` / `StopWallhack`, `WallEnabled`, `WallOccluded`, `WallVisible`, `RefreshWallSettings`, `SetWallColor`, `SetWall`.

### ESP / VIP Shot ESP
`g_vipserver_VIPShotESP`, `g_vipserver_ESPOptions`, `g_vipserver_TrackedCharacters`, `g_Botmater_VIPShotESP`, `__VIPShotESP*Runner/Cleanup`, `GetESPAll`/`SetESPAll`, `HealthBars`, `HealthBg`, `HasHead`, `WorldHead`, `BoneMeshes`, `BonePoints`, `VIPShotFastRunner`, `latencyScope`.

### Deteksi & manipulasi bot
`bIsABot`, `bIsBot`, `IsBot`, `BotLow`, `BotMid`, `BotBG`, `BotText`, `BotCount`, `_LastBots`, `_BotCache`, `headshotRate`.

### Render/UI (engine UE4 via canvas)
`IpadView`, `IpadViewFOV`, `ViewportW/H`, `RawViewportW/H`, `CanvasOffsetX/Y`, `FLinearColor`, `SetBrushColor`, `ColorAndOpacity`, `TemplateColorAndOpacity`, `HealthFill`, `HeaderStyled`, `HackMenu`, `HackMenuInitialized`, `LunarUIAssetCache`.

### Keamanan & VIP licensing
`VIPLicenseLogin/Logout/Status`, `LunarLoginRuntime`, `IsAuthorized`, `Authorized`, `sessionAuthorized`, `AuthLocked`, `VIPLicenseStatus`, `http_manager`, `AttemptKey`, `Token`, `Key`, `GetPhoneDeviceID` (HWID), `DeviceReads`, `LunarSettingsDiagnostics`, `LunarOptionalStartupError`.
- Menu = **SIGN-IN/VIP-server**: script ini butuh login/token; ada sistem lisensi aktif + anti-analisis `HookInstalled`/`__akhooked`.

### Blok data identitas (hex)
RATUSAN string GUID hex (contoh: `380352a5b407...`, `c0dbaa0d1c17cee1...`, `b01bd2755cef...`) — kemungkinan siggy table/ID offset (tidak dianalisis lanjutan), plus hex pendek (14-24 char) = config/checksum.

## 5. Yang Belum Terpecahkan

1. **Opcode permutation** — pemetaan bytecode → opcode Lua standar butuh statistik besar atau binary loader runtime (memiliki tabel). Efek: code logika yang sebenarnya (urutan eksekusi fitur, tuning algoritma) belum bisa dibaca.
2. **`game_patch_4.6.1.21605.pak`** — encrypted full-file (entropy ~7.x/8 semua blok, tanpa magic). Mungkin berisi mod_menu FILE (offset table/memory patch) yang sesungguhnya. Butuh loader dari aplikasi YogzzMods (APK "YogzzMods GL 32BIT" di channel mereka) untuk traceback kunci/decryptor.
3. **156 string panjang ter-garble** (layer-2) — kemungkinan embedded embedded asset template.

## 6. Artefak

- `~/REA_FREEYAHIKO/RE_REPORT.md` — laporan ini
- `~/REA_FREEYAHIKO/decoded_strings.json` — hasil dekripsi string (latin1)
- `~/REA_FREEYAHIKO/xorkey32.txt` — kunci 32-byte (hex)
- `~/REA_FREEYAHIKO/allstrings.json` — raw ciphertext (offset + hex)
- `~/REA_FREEYAHIKO/chains.json` — peta tabel konstanta (offset)
- `~/REA_FREEYAHIKO/report_data.txt` — dump berkas berkaitan fitur
- `~/lundump.py, scanB.py, padsolve*.py, fixkey*.py, finaldec.py` — toolchain analisis
- `~/FREEYAHIKO.lua` — salinan file sumber

## 7. Cara Menghapus Proteksi (ilustratif, untuk analisis)

```python
key32 = bytes.fromhex("112136474657a78d9d8490d8ab008c35261af7e45805b8b31507d02c1e8ff6c8")
plain = bytes(c ^ key32[i % 32] for i, c in enumerate(cipher))
```
Diterapkan ke tiap konstanta string di dump (posisi di chains.json).

# sesuaikan: 11 21 36 47 46 57 a7 8d 9d 84 90 d8 ab 00 8c 35 26 1a f7 e4 58 05 b8 b3 15 07 d0 2c 1e 8f f6 c8
plain = bytes(c ^ key32[i % 32] for i, c in enumerate(cipher))
```

Diterapkan ke tiap konstanta string di dump (posisi tercatat di chains.json).

## 8. Catatan Etika/Keamanan

Semua analisis statis eksekusi dan tidak ada file yang dijalankan atau di-distribusi ulang. Cheat bergantung pada login/VIP server pihak ketiga — penggunaan juga berisiko (token/HWID dikirim via `http_manager`).
