#!/usr/bin/env python3
# coding=utf-8
import re
import pandas as pd
import os

# ------------------------
# 1️⃣ 解析 .adoc 文件
# ------------------------
def parse_adoc(adoc_file):
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
    return results

# ------------------------
# 2️⃣ 解析 Excel 文件
# ------------------------
def parse_excel(excel_file):
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
    return opcode_map

# ------------------------
# 3️⃣ 合并数据并生成结果
# ------------------------
def merge_adoc_excel(adoc_entries, opcode_map):
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

    return results

# ------------------------
# 4️⃣ 主函数：整合流程
# ------------------------
def generate_instruction_excel(adoc_file, excel_file, output_excel="result.xlsx"):
    adoc_entries = parse_adoc(adoc_file)
    opcode_map = parse_excel(excel_file)
    merged_results = merge_adoc_excel(adoc_entries, opcode_map)

    if not merged_results:
        print("⚠ 未解析到任何结果，请检查 adoc 与 Excel 是否匹配前缀")
        return False

    df_out = pd.DataFrame(merged_results)
    df_out.to_excel(output_excel, index=False)
    print("🎉 生成完成：", os.path.abspath(output_excel))
    return True

# ------------------------
# 5️⃣ 脚本直接运行
# ------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python script.py input.adoc opcode.xlsx [output.xlsx]")
        sys.exit(1)

    adoc_file = sys.argv[1]
    excel_file = sys.argv[2]
    output_excel = sys.argv[3] if len(sys.argv) > 3 else "result.xlsx"

    generate_instruction_excel(adoc_file, excel_file, output_excel)

