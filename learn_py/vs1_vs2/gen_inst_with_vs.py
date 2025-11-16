#!/usr/bin/env python3
# coding=utf-8
import re
import csv
import sys
import os
import pandas as pd

def extract_tables_from_adoc(adoc_file):
    """从 .adoc 文件提取所有表格的数据"""
    with open(adoc_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"\|===\s*(.*?)\|==="  # 匹配每个表格内容（非贪婪）
    tables = re.findall(pattern, content, re.S)

    adoc_entries = []

    for table in tables:
        rows = table.strip().split("\n")
        for row in rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if len(cells) == 2:
                funct6, mnemonic = cells
                # print((funct6, mnemonic))
                adoc_entries.append((funct6, mnemonic))

    return adoc_entries

def load_excel(excel_file):
    """
    直接加载 Excel 文件，返回 assembly 与 funct6 列表
    输入：
        excel_file : str - Excel 文件路径
    输出：
        List[Tuple[str, str]] - [(funct6, assembly), ...]
    """
    df = pd.read_excel(excel_file)

    # 确保列名匹配
    assembly_col = "assembly"
    funct6_col = "funct6"
    if "funtc3" in df.columns:
        funct3_col = "funtc3"
    elif "funct3" in df.columns:
        funct3_col = "funct3"
    else:
        funct3_col = None

    entries = []
    for _, row in df.iterrows():
        assembly = str(row[assembly_col]).strip()
        funct6 = str(row[funct6_col]).strip()
        entries.append((funct6, assembly))

    return entries
def load_excel_csv(csv_file):
    """加载 Excel 转换后的 CSV 内容"""
    csv_entries = []

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assembly = row.get("assembly", "").strip()
            funct6 = row.get("funct6", "").strip()
            csv_entries.append((funct6, assembly))

    return csv_entries


def merge_sources(adoc_file, csv_file, output_file="merged_output.txt"):
    """主功能函数：合并 adoc 和 excel 两个来源"""
    print("📌 Parsing ADOC...")
    adoc_entries = extract_tables_from_adoc(adoc_file)
    adoc_dict = {f: m for f, m in adoc_entries}

    print("📌 Parsing CSV (converted from Excel)...")
    csv_entries = load_excel_csv(csv_file)
    csv_dict = {f: m for f, m in csv_entries}

    print("📌 Merging results...")
    all_keys = sorted(set(adoc_dict.keys()) | set(csv_dict.keys()))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("funct6  | From ADOC | From Excel\n")
        f.write("-----------------------------------\n")

        for key in all_keys:
            v1 = adoc_dict.get(key)
            v2 = csv_dict.get(key)

            if v1 and v2:
                src = "1 & 3 ✅"
            elif v1:
                src = "1 ❌"
            elif v2:
                src = "3 ❌"
            else:
                src = "UNKNOWN"

            f.write(f"{key:6} | {v1 or '-':10} | {v2 or '-':15} | {src}\n")

    print(f"🎉 Done! Result saved to: {output_file}")


# 运行脚本时自动执行
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py input.adoc input.csv [output.txt]")
        sys.exit(1)

    adoc_file = sys.argv[1]
    csv_file = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else "merged_output.txt"

    merge_sources(adoc_file, csv_file, output)

