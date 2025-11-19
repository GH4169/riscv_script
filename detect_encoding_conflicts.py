#!/usr/bin/env python3
# coding: utf-8
import re


def parse_encoding(line, lineno):
    m = re.search(r"\{32'b([^}]+)\}", line)
    if not m:
        return None

    raw = m.group(1)

    if not re.fullmatch(r"[01_?]+", raw):
        raise ValueError(f"[Line {lineno}] Invalid characters: {raw}")

    code = raw.replace("_", "")

    if len(code) != 32:
        raise ValueError(f"[Line {lineno}] Length != 32 bits: {code}")

    return code


def encode_mask(code):
    bit_val = []
    bit_mask = []
    for c in code:
        if c == '?':
            bit_val.append('0')
            bit_mask.append('0')
        else:
            bit_val.append(c)
            bit_mask.append('1')
    return int("".join(bit_val), 2), int("".join(bit_mask), 2)


def conflict_mask_mask(m1_val, m1_bits, m2_val, m2_bits):
    return (m1_val & m2_bits) == (m2_val & m1_bits)


def detect_conflicts(filename):
    """
    Return: list of conflict pairs:
    [ ((code1, line1), (code2, line2)), ... ]
    """
    full_codes = {}  # val -> (code, lineno)
    masks = []       # (val, bits, code, lineno)
    duplicates = []

    with open(filename, "r") as f:
        for idx, line in enumerate(f, 1):
            code = parse_encoding(line, idx)
            if not code:
                continue

            if '?' not in code:
                val = int(code, 2)
                if val in full_codes:
                    duplicates.append(((code, idx), full_codes[val]))
                else:
                    full_codes[val] = (code, idx)
            else:
                m_val, m_bits = encode_mask(code)
                masks.append((m_val, m_bits, code, idx))

    # mask ↔ full
    for m_val, m_bits, m_code, m_lineno in masks:
        for f_val, (f_code, f_lineno) in full_codes.items():
            if (f_val & m_bits) == m_val:
                duplicates.append(((m_code, m_lineno), (f_code, f_lineno)))

    # mask ↔ mask
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            mv1, mb1, c1, l1 = masks[i]
            mv2, mb2, c2, l2 = masks[j]
            if conflict_mask_mask(mv1, mb1, mv2, mb2):
                duplicates.append(((c1, l1), (c2, l2)))

    return duplicates


# Optional CLI wrapper (still usable)
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input_file")
        sys.exit(1)

    conflicts = detect_conflicts(sys.argv[1])

    if conflicts:
        print("========= Found Conflicts =========")
        for (c1, l1), (c2, l2) in conflicts:
            print(f"[Line {l1}] {c1}  <==>  [Line {l2}] {c2}\n")
    else:
        print("No conflicts found.")
