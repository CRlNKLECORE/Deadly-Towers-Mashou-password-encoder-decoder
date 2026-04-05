#!/usr/bin/env python3
from dataclasses import dataclass, asdict
from typing import Dict, List
import argparse
import json

ALPHABET = "." + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "12345"
CHAR_TO_VAL: Dict[str, int] = {ch: i for i, ch in enumerate(ALPHABET)}
VAL_TO_CHAR: Dict[int, str] = {i: ch for i, ch in enumerate(ALPHABET)}


def hx(v: int, w: int = 2) -> str:
    return f"0x{v:0{w}X}"


@dataclass
class PackedPayload:
    p0_bells: int
    p1_flags: int
    p2_max_hp_low: int
    p3_equipment_locals: int
    p4_misc_and_noise: int


@dataclass
class DecodedFields:
    bells: int

    fireball_bell_local: int
    fireball_bell_runtime: int

    magic_key_local: int
    magic_key_runtime: int

    boots_local: int
    boots_runtime: int

    hp_low: int

    helmet_local: int
    shield_local: int
    armor_local: int
    weapon_local: int

    helmet_runtime: int
    shield_runtime: int
    armor_runtime: int
    weapon_runtime: int

    shot_upgrade_local: int
    shot_upgrade_runtime: int

    gauntlet_local: int
    gauntlet_runtime: int

    raw_p4_high_nibble: int

    checksum: int
    checksum_valid: bool


def normalize_password(pw: str) -> str:
    pw = pw.strip().upper()
    if len(pw) != 10:
        raise ValueError("Password must be 10 characters")
    for ch in pw:
        if ch not in CHAR_TO_VAL:
            raise ValueError(f"Invalid password character: {ch!r}")
    return pw


def text_to_symbols(pw: str) -> List[int]:
    pw = normalize_password(pw)
    return [CHAR_TO_VAL[ch] for ch in pw]


def bit_slice_inverse(symbols: List[int]) -> List[int]:
    q = [0, 0, 0, 0, 0]  # $0108-$010C
    for bit_index in range(8):
        s = symbols[bit_index] & 0x1F
        for q_index in range(5):
            q[q_index] |= ((s >> q_index) & 1) << bit_index
    return q


def recover_payload(symbols: List[int]) -> PackedPayload:
    q0, q1, q2, q3, q4 = bit_slice_inverse(symbols)

    p4 = (q4 + 0xAA) & 0xFF
    p0 = (q0 - p4 + 1) & 0xFF
    p1 = (q1 - p4 + 1) & 0xFF
    p2 = (q2 - p4 + 1) & 0xFF
    p3 = (q3 - p4 + 1) & 0xFF

    return PackedPayload(
        p0_bells=p0,
        p1_flags=p1,
        p2_max_hp_low=p2,
        p3_equipment_locals=p3,
        p4_misc_and_noise=p4,
    )


def decode_fields(symbols: List[int]) -> DecodedFields:
    payload = recover_payload(symbols)

    low5 = symbols[8] & 0x1F
    hi_raw = symbols[9] & 0x1F
    hi3 = hi_raw & 0x07
    checksum = low5 | (hi3 << 5)

    calc = (
        payload.p0_bells
        + payload.p1_flags
        + payload.p2_max_hp_low
        + payload.p3_equipment_locals
        + payload.p4_misc_and_noise
    ) & 0xFF

    p1 = payload.p1_flags
    p3 = payload.p3_equipment_locals
    p4 = payload.p4_misc_and_noise

    fireball_local = p1 & 0x07
    fireball_runtime = fireball_local

    magic_key_local = (p1 >> 3) & 0x01
    magic_key_runtime = 0x01 if magic_key_local else 0x00

    boots_local = (p1 >> 4) & 0x01
    boots_runtime = 0x02 if boots_local else 0x00

    helmet_local = p3 & 0x03
    shield_local = (p3 >> 2) & 0x03
    armor_local = (p3 >> 4) & 0x03
    weapon_local = (p3 >> 6) & 0x03

    helmet_runtime = 0x01 + helmet_local
    shield_runtime = 0x05 + shield_local
    armor_runtime = 0x09 + armor_local
    weapon_runtime = 0x0D + weapon_local

    shot_upgrade_local = p4 & 0x03
    shot_upgrade_runtime = {
        0: 0x00,
        1: 0x19,
        2: 0x1A,
        3: 0x1B,
    }[shot_upgrade_local]

    gauntlet_local = (p4 >> 2) & 0x03
    gauntlet_runtime = {
        0: 0x00,
        1: 0x16,
        2: 0x17,
        3: 0x18,
    }[gauntlet_local]

    return DecodedFields(
        bells=payload.p0_bells,

        fireball_bell_local=fireball_local,
        fireball_bell_runtime=fireball_runtime,

        magic_key_local=magic_key_local,
        magic_key_runtime=magic_key_runtime,

        boots_local=boots_local,
        boots_runtime=boots_runtime,

        hp_low=payload.p2_max_hp_low,

        helmet_local=helmet_local,
        shield_local=shield_local,
        armor_local=armor_local,
        weapon_local=weapon_local,

        helmet_runtime=helmet_runtime,
        shield_runtime=shield_runtime,
        armor_runtime=armor_runtime,
        weapon_runtime=weapon_runtime,

        shot_upgrade_local=shot_upgrade_local,
        shot_upgrade_runtime=shot_upgrade_runtime,

        gauntlet_local=gauntlet_local,
        gauntlet_runtime=gauntlet_runtime,

        raw_p4_high_nibble=p4 & 0xF0,

        checksum=checksum,
        checksum_valid=(checksum == calc),
    )


def to_hex_dict(obj):
    d = asdict(obj)
    out = {}
    for k, v in d.items():
        if isinstance(v, bool):
            out[k] = v
        elif isinstance(v, int):
            out[k] = hx(v)
        else:
            out[k] = v
    return out


def decode_password(pw: str):
    symbols = text_to_symbols(pw)
    payload = recover_payload(symbols)
    fields = decode_fields(symbols)

    return {
        "password": normalize_password(pw),
        "symbols": [hx(x) for x in symbols],
        "payload": to_hex_dict(payload),
        "decoded": to_hex_dict(fields),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("password", help="10-character Deadly Towers password")
    args = parser.parse_args()

    result = decode_password(args.password)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()