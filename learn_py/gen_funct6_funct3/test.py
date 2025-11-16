input_data = """|===                 
| 000000 |V|X|I| vadd
| 000001 | | | |     
| 000010 |V|X| | vsub"""

# 列标记到 OP 映射
col_map = {"V": "OPIVV", "X": "OPIVX", "I": "OPIVI"}

output_lines = []

for line in input_data.splitlines():
    line = line.strip()
    if not line or line.startswith("|==="):
        continue

    # 分割列
    parts = [p.strip() for p in line.split("|")[1:]]
    if len(parts) < 5:
        continue

    code, v_col, x_col, i_col, mnemonic = parts[:5]
    cols = [v_col, x_col, i_col]
    print(cols)

    # 针对每列生成对应输出
    print(list(zip(cols, ["V", "X", "I"])))
    for col, name in zip(cols, ["V", "X", "I"]):
        if col:  # 只有非空才输出
            op = col_map[name]
            output_lines.append(f"{mnemonic}_{op} {code} {op}")

# 输出最终结果
print("\n".join(output_lines))

input_data = """|===
| 000000 |V|X|I| vadd       | 000000 |V|X| vredsum     | 000000 |V|F| vfadd
| 000001 | | | |            | 000001 |V| | vredand     | 000001 |V| | vfredusum
| 000010 |V|X| | vsub       | 000010 |V| | vredor      | 000010 |V|F| vfsub"""

output = 
vadd_OPIVV 000000 OPIVV
vadd_OPIVX 000000 OPIVX
vadd_OPIVI 000000 OPIVI
vsub_OPIVV 000010 OPIVV
vsub_OPIVX 000010 OPIVX

vredsum_OPMVV 000000 OPMVV
vredsum_OPMVX 000000 OPMVX
vredand_OPMVV 000001 OPMVV
vredor_OPMVV 000010 OPMVV

vfadd_OPFVV 000000 OPFVV
vfadd_OPFVF 000000 OPFVF
vfredusum_OPFVV 000001 OPFVV
fvsub_OPFVV 000010 OPFVV
fvsub_OPFVV 000010 OPFVF
