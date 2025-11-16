#!/usr/bin/env python3
# coding=utf-8

import re
import sys
import pandas as pd

# ======================
# 解析 .adoc 文件
# ======================

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
    # print(f"adoc_entries: {results}")
    return results

# ======================
# 解析 Excel
# ======================
def parse_excel(excel_file):
    """
    返回：
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

        if assembly.lower() == "nan":
            continue
        prefix = assembly.split("_")[0]
        opcode_map[prefix] = (assembly, funct6, funct3)

    # print(f"opcode_map: {opcode_map}")
    return opcode_map


# ======================
# 合并数据
# ======================
def merge_adoc_excel(adoc_entries, opcode_map):
    merged = []
    adoc_keys = {entry["type"] for entry in adoc_entries}
    print(f"adoc_keys = {adoc_keys}")
    # 先把 Excel 直接加入结果
    for prefix, (assembly, funct6, funct3) in opcode_map.items():
        if prefix not in adoc_keys: 
            merged.append({
                "assembly": assembly,
                "funct6": funct6,
                "funct3": funct3,
                "vs1": "",
                "vs2": "",
                "vm": ""
            })

    # adoc 生成扩展行
    for entry in adoc_entries:
        type_tmp = entry["type"]
        field = entry["field"]
        bits = entry["bits"]
        mnemonic = entry["mnemonic"]

        if type_tmp not in opcode_map:
            print(f"ERROR: can't find {type_tmp} in excel")
            continue

        _, funct6, funct3 = opcode_map[type_tmp]

        # 新 assembly 名称
        suffix = "vs1" if field == "vs1" else "vs2"
        full_assembly = f"{type_tmp}_{funct3}_{suffix}_{mnemonic}"

        merged.append({
            "assembly": full_assembly,
            "funct6": funct6,
            "funct3": funct3,
            "vs1": bits if field == "vs1" else "",
            "vs2": bits if field == "vs2" else "",
            "vm": ""
        })

    return merged


# ======================
# 主流程入口
# ======================
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python3 merge_adoc_excel.py input.adoc input.xlsx")
        sys.exit(1)

    adoc_file = sys.argv[1]
    excel_file = sys.argv[2]

    adoc_entries = parse_adoc(adoc_file)
    opcode_map = parse_excel(excel_file)

    merged = merge_adoc_excel(adoc_entries, opcode_map)

    df_out = pd.DataFrame(merged)
    df_out.to_excel("merged_output.xlsx", index=False)
    print("输出已保存: merged_output.xlsx")
