#!/usr/bin/python3

import sys
import pandas as pd

def process_file_to_excel(input_file, output_file="output.xlsx"):
    group_info = [
        (["V", "X", "I"], {"V": "OPIVV", "X": "OPIVX", "I": "OPIVI"}, 5),
        (["V", "X"], {"V": "OPMVV", "X": "OPMVX"}, 4),
        (["V", "F"], {"V": "OPFVV", "F": "OPFVF"}, 4),
    ]

    with open(input_file, "r") as f:
        input_data = f.read()

    group_outputs = [[] for _ in group_info]

    for line in input_data.splitlines():
        line = line.strip()
        if not line or line.startswith("|==="):
            continue

        parts = [p.strip() for p in line.split("|")]
        if parts and parts[0] == '':
            parts = parts[1:]
        if parts and parts[-1] == '':
            parts = parts[:-1]

        idx = 0
        for g, (col_names, col_map, group_len) in enumerate(group_info):
            if idx + group_len <= len(parts):
                code = parts[idx]
                cols = parts[idx+1:idx+1+len(col_names)]
                mnemonic = parts[idx+1+len(col_names)]

                for col_value, name in zip(cols, col_names):
                    if col_value:
                        op = col_map.get(name)
                        if op:
                            group_outputs[g].append([f"{mnemonic}_{op}", code, op])

            idx += group_len

    # 将所有组合并为一个列表
    all_rows = []
    for out in group_outputs:
        all_rows.extend(out)
        # all_rows.append(["", "", ""])  # 每组后空行

    # 写入 Excel
    # df = pd.DataFrame(all_rows, columns=["assembly", "funct6", "funct3", "vs1", "vs2", "vm"])
    df = pd.DataFrame(all_rows, columns=["assembly", "funct6", "funct3"])
    df["vs1"] = ""
    df["vs2"] = ""
    df["vm"] = ""
    df.to_excel(output_file, index=False)
    print(f"Excel saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input_file [output_file.xlsx]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.xlsx"
    process_file_to_excel(input_file, output_file)

