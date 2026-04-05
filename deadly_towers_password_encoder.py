#!/usr/bin/env python3
from __future__ import annotations

from typing import Dict, List
import argparse
import json

ALPHABET = "." + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "12345"
CHAR_TO_VAL: Dict[str, int] = {ch: i for i, ch in enumerate(ALPHABET)}
VAL_TO_CHAR: Dict[int, str] = {i: ch for i, ch in enumerate(ALPHABET)}


def hx(v: int, w: int = 2) -> str:
    return f"0x{v:0{w}X}"


def parse_hex_byte(s: str) -> int:
    s = s.strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    v = int(s, 16)
    if not 0 <= v <= 0xFF:
        raise ValueError("byte out of range")
    return v


def parse_hex_nibble_aligned(s: str) -> int:
    v = parse_hex_byte(s)
    if v & 0x0F:
        raise ValueError("value must end in 0, e.g. 00, 10, A0, F0")
    return v


def choose(prompt: str, allowed: List[int], default: int | None = None) -> int:
    allowed_hex = ", ".join(hx(v) for v in allowed)
    default_text = f" [{hx(default)}]" if default is not None else ""
    while True:
        raw = input(f"{prompt} ({allowed_hex}){default_text}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            v = parse_hex_byte(raw)
        except Exception:
            print("  Invalid hex byte")
            continue
        if v not in allowed:
            print("  Value outside allowed range")
            continue
        return v


def ask_hex_byte(prompt: str, default: int = 0x00) -> int:
    while True:
        raw = input(f"{prompt} [{hx(default)}]: ").strip()
        if raw == "":
            return default
        try:
            return parse_hex_byte(raw)
        except Exception:
            print("  Invalid hex byte")


def ask_hex_nibble(prompt: str, default: int = 0x00) -> int:
    while True:
        raw = input(f"{prompt} (00,10,20,...,F0) [{hx(default)}]: ").strip()
        if raw == "":
            return default
        try:
            return parse_hex_nibble_aligned(raw)
        except Exception:
            print("  Invalid aligned high-nibble byte")


def encode_p1(fireball_runtime: int, magic_key_runtime: int, boots_runtime: int, hp_hi_class: int) -> int:
    fireball_local = fireball_runtime & 0x07
    magic_key_local = 1 if magic_key_runtime == 0x01 else 0
    boots_local = 1 if boots_runtime == 0x02 else 0
    hp_hi_local = hp_hi_class & 0x03
    return (
        (fireball_local)
        | (magic_key_local << 3)
        | (boots_local << 4)
        | (hp_hi_local << 5)
    ) & 0xFF


def localize_equipment(helmet: int, shield: int, armor: int, weapon: int) -> tuple[int, int, int, int]:
    return (helmet - 0x01, shield - 0x05, armor - 0x09, weapon - 0x0D)


def encode_p3(helmet: int, shield: int, armor: int, weapon: int) -> int:
    h, s, a, w = localize_equipment(helmet, shield, armor, weapon)
    return (h | (s << 2) | (a << 4) | (w << 6)) & 0xFF


def localize_shot_upgrade(runtime: int) -> int:
    mapping = {0x00: 0, 0x19: 1, 0x1A: 2, 0x1B: 3}
    return mapping[runtime]


def localize_gauntlet(runtime: int) -> int:
    mapping = {0x00: 0, 0x16: 1, 0x17: 2, 0x18: 3}
    return mapping[runtime]


def encode_p4(shot_upgrade_runtime: int, gauntlet_runtime: int, timer_noise_hi_nibble: int) -> int:
    shot_local = localize_shot_upgrade(shot_upgrade_runtime)
    gauntlet_local = localize_gauntlet(gauntlet_runtime)
    return (timer_noise_hi_nibble & 0xF0) | ((gauntlet_local & 0x03) << 2) | (shot_local & 0x03)


def payload_to_transformed(p0: int, p1: int, p2: int, p3: int, p4: int) -> tuple[int, int, int, int, int, int]:
    checksum = (p0 + p1 + p2 + p3 + p4) & 0xFF
    q0 = (p0 + p4 - 1) & 0xFF
    q1 = (p1 + p4 - 1) & 0xFF
    q2 = (p2 + p4 - 1) & 0xFF
    q3 = (p3 + p4 - 1) & 0xFF
    q4 = (p4 - 0xAA) & 0xFF
    return q0, q1, q2, q3, q4, checksum


def transformed_to_symbols(q0: int, q1: int, q2: int, q3: int, q4: int, checksum: int, checksum_noise_0x18: int) -> List[int]:
    syms: List[int] = []
    for bit in range(8):
        s = (
            (((q0 >> bit) & 1) << 0)
            | (((q1 >> bit) & 1) << 1)
            | (((q2 >> bit) & 1) << 2)
            | (((q3 >> bit) & 1) << 3)
            | (((q4 >> bit) & 1) << 4)
        )
        syms.append(s & 0x1F)
    syms.append(checksum & 0x1F)
    syms.append((((checksum >> 5) & 0x07) | (checksum_noise_0x18 & 0x18)) & 0x1F)
    return syms


def symbols_to_text(symbols: List[int]) -> str:
    return "".join(VAL_TO_CHAR[s & 0x1F] for s in symbols)


def build_password(
    bells: int,
    fireball_runtime: int,
    magic_key_runtime: int,
    boots_runtime: int,
    hp_hi_class: int,
    hp_low: int,
    helmet: int,
    shield: int,
    armor: int,
    weapon: int,
    shot_upgrade_runtime: int,
    gauntlet_runtime: int,
    timer_noise_hi_nibble: int,
    checksum_noise_0x18: int,
) -> dict:
    p0 = bells
    p1 = encode_p1(fireball_runtime, magic_key_runtime, boots_runtime, hp_hi_class)
    p2 = hp_low
    p3 = encode_p3(helmet, shield, armor, weapon)
    p4 = encode_p4(shot_upgrade_runtime, gauntlet_runtime, timer_noise_hi_nibble)
    q0, q1, q2, q3, q4, checksum = payload_to_transformed(p0, p1, p2, p3, p4)
    syms = transformed_to_symbols(q0, q1, q2, q3, q4, checksum, checksum_noise_0x18)
    return {
        "payload": [p0, p1, p2, p3, p4],
        "transformed": [q0, q1, q2, q3, q4],
        "checksum": checksum,
        "symbols": syms,
        "password": symbols_to_text(syms),
    }


def interactive() -> None:
    print("Deadly Towers password crafter")
    print("All values are entered in hex. Press Enter to accept the default shown.")
    print("Use 00 for both noise inputs to get a stable password shape.\n")

    bells = ask_hex_byte("bells / $01B1")
    fireball = choose("fireball bell / $01B4", list(range(0x00, 0x08)), 0x00)
    magic_key = choose("magic key runtime / $01B5", [0x00, 0x01], 0x00)
    boots = choose("boots runtime / $01B0", [0x00, 0x02], 0x00)
    hp_hi_class = choose("HP-high class bits (packed only, not raw runtime byte)", [0x00, 0x01, 0x02, 0x03], 0x00)
    hp_low = ask_hex_byte("HP low byte / $01B3")

    print()
    helmet = choose("helmet runtime / $0170", [0x01, 0x02, 0x03, 0x04], 0x01)
    shield = choose("shield runtime / $0171", [0x05, 0x06, 0x07, 0x08], 0x05)
    armor = choose("armor runtime / $0172", [0x09, 0x0A, 0x0B, 0x0C], 0x09)
    weapon = choose("weapon runtime / $0173", [0x0D, 0x0E, 0x0F, 0x10], 0x0D)
    shot_upgrade = choose("shot upgrade runtime / $0174", [0x00, 0x19, 0x1A, 0x1B], 0x00)
    gauntlet = choose("gauntlet runtime / $0175", [0x00, 0x16, 0x17, 0x18], 0x00)

    print()
    timer_noise_hi_nibble = ask_hex_nibble("$09 high nibble mixed into $0104", 0x00)
    checksum_noise_0x18 = choose("extra checksum noise bits ($09 & 0x18)", [0x00, 0x08, 0x10, 0x18], 0x00)

    result = build_password(
        bells=bells,
        fireball_runtime=fireball,
        magic_key_runtime=magic_key,
        boots_runtime=boots,
        hp_hi_class=hp_hi_class,
        hp_low=hp_low,
        helmet=helmet,
        shield=shield,
        armor=armor,
        weapon=weapon,
        shot_upgrade_runtime=shot_upgrade,
        gauntlet_runtime=gauntlet,
        timer_noise_hi_nibble=timer_noise_hi_nibble,
        checksum_noise_0x18=checksum_noise_0x18,
    )

    print("\nPassword:", result["password"])
    print("Payload:", [hx(x) for x in result["payload"]])
    print("Transformed:", [hx(x) for x in result["transformed"]])
    print("Checksum:", hx(result["checksum"]))
    print("Symbols:", [hx(x) for x in result["symbols"]])


def main() -> None:
    parser = argparse.ArgumentParser(description="Craft Deadly Towers passwords from runtime-style inputs")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of interactive prompt")
    parser.add_argument("--bells")
    parser.add_argument("--fireball")
    parser.add_argument("--magic-key")
    parser.add_argument("--boots")
    parser.add_argument("--hp-hi-class")
    parser.add_argument("--hp-low")
    parser.add_argument("--helmet")
    parser.add_argument("--shield")
    parser.add_argument("--armor")
    parser.add_argument("--weapon")
    parser.add_argument("--shot-upgrade")
    parser.add_argument("--gauntlet")
    parser.add_argument("--timer-noise-hi")
    parser.add_argument("--checksum-noise")
    args = parser.parse_args()

    provided = any(getattr(args, k.replace('-', '_')) is not None for k in [
        'bells','fireball','magic_key','boots','hp_hi_class','hp_low','helmet','shield','armor','weapon','shot_upgrade','gauntlet','timer_noise_hi','checksum_noise'
    ])

    if not provided:
        interactive()
        return

    vals = {
        "bells": parse_hex_byte(args.bells or "00"),
        "fireball_runtime": parse_hex_byte(args.fireball or "00"),
        "magic_key_runtime": parse_hex_byte(args.magic_key or "00"),
        "boots_runtime": parse_hex_byte(args.boots or "00"),
        "hp_hi_class": parse_hex_byte(args.hp_hi_class or "00"),
        "hp_low": parse_hex_byte(args.hp_low or "00"),
        "helmet": parse_hex_byte(args.helmet or "01"),
        "shield": parse_hex_byte(args.shield or "05"),
        "armor": parse_hex_byte(args.armor or "09"),
        "weapon": parse_hex_byte(args.weapon or "0D"),
        "shot_upgrade_runtime": parse_hex_byte(args.shot_upgrade or "00"),
        "gauntlet_runtime": parse_hex_byte(args.gauntlet or "00"),
        "timer_noise_hi_nibble": parse_hex_nibble_aligned(args.timer_noise_hi or "00"),
        "checksum_noise_0x18": parse_hex_byte(args.checksum_noise or "00"),
    }
    result = build_password(**vals)
    out = {
        **{k: hx(v) for k, v in vals.items()},
        "payload": [hx(x) for x in result["payload"]],
        "transformed": [hx(x) for x in result["transformed"]],
        "checksum": hx(result["checksum"]),
        "symbols": [hx(x) for x in result["symbols"]],
        "password": result["password"],
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for k, v in out.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
