# Deadly Towers Password Encoder / Decoder

Reverse engineered password system for **Deadly Towers (NES)**.

This project provides tools and documentation to:

- Decode passwords into structured game state
- Encode controlled game state into valid passwords
- Understand how the game compresses and reconstructs player data

---

# Overview

Deadly Towers uses a **10-character password system** built from a custom 5-bit alphabet.

Internally:

- Password characters are stored at `$0100–$0109`
- Each character represents a **5-bit value (0x00–0x1F)**

Alphabet mapping:


00 = .

01–1A = A–Z

1B–1F = 1–5


---

# High-Level Flow

The password system works in three stages:


Runtime State
↓
Packed Payload (5 bytes)
↓
Transform / Obfuscation
↓
Bit-Sliced Symbols (10 bytes)
↓
Displayed Password


---

# Packed Payload Layout

## $0100 — Bells (Raw)


$0100 = $01B1


- Fully raw byte
- One of the best controlled inputs

---

## $0101 — Bitfield

Built from multiple values:

- `$01B4` Fireball bell (3 bits)
- `$01B5` Magic key (1 bit)
- `$01B0` Boots (1 bit)
- `$01B2` Partial HP bits (2 bits)

Bit layout:


bit 7 = 0
bit 6 = HP bit 1
bit 5 = HP bit 0
bit 4 = Boots
bit 3 = Magic key
bit 2–0 = Fireball bell


---

## $0102 — HP Low Byte (Raw)


$0102 = $01B3


- Directly preserved
- Overflow behavior observed

---

## $0103 — Equipment (Packed 2-bit fields)

Each equipment piece is normalized into a **0–3 local value**:

| Item   | Runtime Range | Local |
|--------|--------------|-------|
| Helmet | 01–04        | 0–3   |
| Shield | 05–08        | 0–3   |
| Armor  | 09–0C        | 0–3   |
| Weapon | 0D–10        | 0–3   |

Packed into one byte:


bits 1–0 = helmet
bits 3–2 = shield
bits 5–4 = armor
bits 7–6 = weapon


---

## $0104 — Misc Fields

Low nibble:

- Shot upgrade (`$0174`)
- Gauntlet (`$0175`)

High nibble:

- Derived from `$09`
- Acts as noise / timing-dependent input

---

# Runtime Value Mapping

## Shot Upgrade (`$0174`)

| Local | Runtime |
|------|--------|
| 0    | 00     |
| 1    | 19     |
| 2    | 1A     |
| 3    | 1B     |

---

## Gauntlet (`$0175`)

| Local | Runtime |
|------|--------|
| 0    | 00     |
| 1    | 16     |
| 2    | 17     |
| 3    | 18     |

---

## Boots (`$01B0`)

| Local | Runtime |
|------|--------|
| 0    | 00     |
| 1    | 02     |

---

## Magic Key (`$01B5`)

| Local | Runtime |
|------|--------|
| 0    | 00     |
| 1    | 01     |

---

## Fireball Bell (`$01B4`)


0x00–0x07 (3-bit value)


---

# Transform Stage

After packing, the game computes:

## Checksum


checksum = (p0 + p1 + p2 + p3 + p4) & 0xFF


---

## Derived Bytes


q0 = p0 + p4 - 1
q1 = p1 + p4 - 1
q2 = p2 + p4 - 1
q3 = p3 + p4 - 1
q4 = p4 - 0xAA


(All modulo 256)

---

# Bit-Slice Encoding

The 5 transformed bytes are split into 8 output bytes:


bit i of q0 → bit 0 of output[i]
bit i of q1 → bit 1 of output[i]
bit i of q2 → bit 2 of output[i]
bit i of q3 → bit 3 of output[i]
bit i of q4 → bit 4 of output[i]


Then:


output[8] = checksum & 0x1F
output[9] = (checksum >> 5) + noise


Final output becomes `$0100–$0109`.

---

# Noise / Instability

The system mixes in bits from `$09`, which causes:

- Password variation even when state is identical
- Non-deterministic outputs

### To stabilize:

Set before generating password:


$08 = 00
$09 = 00


---

# Raw vs Normalized Fields

## Raw / High Control

- Bells (`$01B1`)
- HP low (`$01B3`)

## Normalized

- Equipment
- Shot upgrade
- Gauntlet
- Boots
- Magic key
- Fireball bell

These are constrained to small enums or bitfields.

---

# Exploit Notes

The password system allows:


controlled initial game state


But not:


arbitrary memory write


Most realistic path:


crafted password
→ unusual but valid state
→ gameplay systems misbehave
→ corruption / control flow issues


---

# Observed Behavior

- High bell values (`0xFF`) cause rendering corruption
- HP values exhibit wraparound behavior
- Some UI routines do not clamp values properly

This suggests potential for:

- buffer overruns in rendering logic
- unsafe loops using attacker-controlled values

---

# Usage

## Encode

Run:


python deadly_towers_password_encoder.py


Follow prompts or use CLI flags.

---

## Decode

Input a password to extract:

- symbol values
- packed payload
- reconstructed runtime state

---

# Recommended Workflow

1. Start from a clean savestate
2. Zero `$08/$09`
3. Modify one field at a time
4. Compare:
   - runtime RAM
   - packed payload
   - final password

---

# Notes

This implementation is based on:

- ASM analysis
- Emulator tracing (Mesen)
- Controlled RAM experiments

Further work could include:

- full disassembly annotation
- automated exploit search
- deeper analysis of rendering routines

---

# License

MIT
