#!/usr/bin/python3
input_data = """|===
| 000000 |V|X|I| vadd       | 000000 |V|X| vredsum     | 000000 |V|F| vfadd
| 000001 | | | |            | 000001 |V| | vredand     | 000001 |V| | vfredusum
| 000010 |V|X| | vsub       | 000010 |V| | vredor      | 000010 |V|F| vfsub"""

# 每组的列名、OP映射和列数
group_info = [
    (["V", "X", "I"], {"V": "OPIVV", "X": "OPIVX", "I": "OPIVI"}, 5),  # 第一组
    (["V", "X"], {"V": "OPMVV", "X": "OPMVX"}, 4),                     # 第二组
    (["V", "F"], {"V": "OPFVV", "F": "OPFVF"}, 4),                     # 第三组
]

# 每组独立保存输出
group_outputs = [[] for _ in group_info]

for line in input_data.splitlines():
    line = line.strip()
    if not line or line.startswith("|==="):
        continue

    # 拆分列，保留空列，仅去掉首尾空字符串
    parts = [p.strip() for p in line.split("|")]
    if parts and parts[0] == '':
        parts = parts[1:]

    idx = 0
    for g, (col_names, col_map, group_len) in enumerate(group_info):
        if idx + group_len <= len(parts):
            code = parts[idx]
            cols = parts[idx+1:idx+1+len(col_names)]
            mnemonic = parts[idx+1+len(col_names)]

            for col_value, name in zip(cols, col_names):
                if col_value:  # 非空才输出
                    op = col_map.get(name)
                    if op:
                        group_outputs[g].append(f"{mnemonic}_{op} {code} {op}")

        idx += group_len  # 移动到下一组

# 按组顺序打印输出
for out in group_outputs:
    for line in out:
        print(line)
    print()

