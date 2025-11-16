#!/usr/bin/env python3
# coding=utf-8

import sys
import re
import os
import pandas as pd

def process_file_to_excel(input_file, output_file="output.xlsx"):# {{{
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
    print(f"generated: {output_file}")# }}}

def parse_adoc(adoc_file):# {{{
    """
    解析 .adoc 文件，返回列表：
    [
        {"type": "VWXUNARY0", "field": "vs1", "bits": "00000", "mnemonic": "vmv.x.s"},
        ...
    ]
    """
    results = []
    current_type = None
    current_field = None

    with open(adoc_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 匹配表格标题
            m = re.match(r'\.(\w+)\s+encoding space', line)
            if m:
                current_type = m.group(1)
                continue

            # 表头 vs1 / vs2
            if "|  vs1" in line:
                current_field = "vs1"
                continue
            if "|  vs2" in line:
                current_field = "vs2"
                continue

            # 表格行 | 00000 | vmv.s.x
            m = re.match(r'\|\s*([01]{5})\s*\|\s*(\S+)', line)
            if m and current_type and current_field:
                bits, mnemonic = m.groups()
                results.append({
                    "type": current_type,
                    "field": current_field,
                    "bits": bits,
                    "mnemonic": mnemonic
                })
    # print(results)
    return results# }}}

def parse_excel(excel_file):# {{{
    """
    读取 Excel 文件，返回字典：
    {
        "VWXUNARY0": ("VWXUNARY0_OPMVV", "10000", "OPMVV"),
        ...
    }
    """
    df = pd.read_excel(excel_file, dtype=str)

    opcode_map = {}
    for _, row in df.iterrows():
        assembly = str(row["assembly"]).strip()
        funct6 = str(row["funct6"]).strip()
        funct3 = str(row["funct3"]).strip()
        prefix = assembly.split("_")[0]
        opcode_map[prefix] = (assembly, funct6, funct3)
    # print(opcode_map)
    return opcode_map# }}}

def merge_adoc_excel(adoc_entries, opcode_map):# {{{
    """
    合并 adoc 数据和 Excel 数据，返回结果列表
    [
        {"assembly": ..., "funct6": ..., "funct3": ..., "vs1": ..., "vs2": ..., "vm": ""},
        ...
    ]
    """
    results = []

    for entry in adoc_entries:
        typ = entry["type"]
        field = entry["field"]
        bits = entry["bits"]
        mnemonic = entry["mnemonic"]

        if typ not in opcode_map:
            print(f"ERROR: can't find type in excel: {typ}")
            continue  # Excel 中没有对应类型，跳过

        opcode_asm, funct6, funct3 = opcode_map[typ]

        vs1 = bits if field == "vs1" else ""
        vs2 = bits if field == "vs2" else ""

        suffix = "rs1" if vs1 else "rs2"
        assembly = f"{opcode_asm}_{suffix}_{mnemonic}"

        results.append({
            "assembly": assembly,
            "funct6": funct6,
            "funct3": funct3,
            "vs1": vs1,
            "vs2": vs2,
            "vm": ""
        })

    return results# }}}

def generate_instruction_excel(adoc_file, excel_file, output_excel="result.xlsx"):# {{{
    adoc_entries = parse_adoc(adoc_file)
    opcode_map = parse_excel(excel_file)
    merged_results = merge_adoc_excel(adoc_entries, opcode_map)

    if not merged_results:
        print("⚠ 未解析到任何结果，请检查 adoc 与 Excel 是否匹配前缀")
        return False

    df_out = pd.DataFrame(merged_results)
    df_out.to_excel(output_excel, index=False)
    print("generated:", output_excel)
    return True# }}}

def merge_all_inst(file1, file2, output_file):# {{{
    df1 = pd.read_excel(file1, dtype=str)
    df2 = pd.read_excel(file2, dtype=str)
    
    # 过滤掉 assembly 首字母大写的行
    df1_filtered = df1[df1['assembly'].str[0].str.islower()]
    
    # 合并两个表格
    # 注意 df2 默认带标题，不需要再去掉标题行
    all_df = pd.concat([df1_filtered, df2], ignore_index=True)
    
    # 输出 Excel
    all_df.to_excel(output_file, index=False)
    print(f"merged insts file: {output_file}")# }}}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} funct6_funct3.adoc vs1_vs2.adoc")
        sys.exit(1)

    os.makedirs("generated_v_inst", exist_ok=True)

    funct6_funct3 = sys.argv[1]
    funct6_funct3_inst = os.path.join("generated_v_inst", "funct6_funct3_inst.xlsx")
    process_file_to_excel(funct6_funct3, funct6_funct3_inst)


    vs1_vs2 = sys.argv[2]
    vs1_vs2_inst = os.path.join("generated_v_inst", "vs1_vs2_inst.xlsx")
    generate_instruction_excel(vs1_vs2, funct6_funct3_inst, vs1_vs2_inst)

    all_v_inst = os.path.join("generated_v_inst", "all_v_inst.xlsx")
    merge_all_inst(funct6_funct3_inst, vs1_vs2_inst, all_v_inst)

