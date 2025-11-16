#!/usr/bin/env python3
# coding=utf-8
import pandas as pd
import re

# -------------------------------
# 自定义解析 WaveDrom
# -------------------------------
def parse_wavedrom_adoc(file_path):# {{{
    templates = []
    with open(file_path, "r") as f:
        data = f.read()

    # 按 {reg: 分段
    blocks = data.split("{reg:")
    for blk in blocks[1:]:
        blk = blk.strip()
        # 去掉开头和结尾的 []
        blk = blk.lstrip('[').rstrip(']}')

        # 提取每个字段行
        fields = []
        lines = blk.splitlines()
        for line in lines:
            line = line.strip().rstrip(",")
            if not line or line.startswith("//"):
                continue

            # 匹配 bits、name、type、attr
            m_bits = re.search(r'bits\s*:\s*(\d+)', line)
            m_name = re.search(r'name\s*:\s*(.*?)(,|})', line)
            m_type = re.search(r'type\s*:\s*(\d+)', line)
            m_attr = re.search(r'attr\s*:\s*(.*?)(}|$)', line)

            field = {}
            if m_bits:
                field['bits'] = int(m_bits.group(1))
            if m_name:
                # 去掉引号和空格
                name = m_name.group(1).strip()
                name = name.strip("'\"")
                name = name.replace("/", "_").replace("[", "_").replace("]", "_")
                field['name'] = name
            if m_type:
                field['type'] = int(m_type.group(1))
            if m_attr:
                attr = m_attr.group(1).strip()
                if attr.startswith("[") and attr.endswith("]"):
                    attr = attr[1:-1].strip()
                attr = attr.strip("'\"")
                # 如果是列表格式 ['OPIVI']
                if attr.startswith('[') and attr.endswith(']'):
                    attr = [a.strip("'\" ") for a in attr[1:-1].split(",")]
                field['attr'] = attr

            fields.append(field)

        templates.append({"reg": fields})
        # print({"reg": fields})
    # print(templates)
    return templates# }}}

# -------------------------------
# 生成 32bit code
# -------------------------------
def generate_code(row, templates):
    funct3_val = str(row['funct3'])
    template = None
    for t in templates:
        attr = t["reg"][0].get("attr")
        if isinstance(attr, list):
            print("ttt")
            if funct3_val in attr:
                template = t
                break
        else:
            if funct3_val == attr:
                template = t
                break
    if not template:
        return "NoTemplate"

    bits_list = []
    for field in template["reg"]:
        name = field["name"]
        width = field["bits"]

        # 固定值（数字或 0x开头）
        if name.isdigit():
            bits = f"{int(name):0{width}b}"
        elif name.startswith("0x"):
            bits = f"{int(name,16):0{width}b}"
        else:
            # Excel 对应列
            col_name = name
            if col_name not in row or pd.isna(row[col_name]) or row[col_name]=="":
                bits = "?" * width
            else:
                val = str(row[col_name])
                if len(val) < width:
                    val = val.rjust(width, "?")
                bits = val
        bits_list.append(bits)

    return "32'b" + "_".join(bits_list)

# -------------------------------
# 主流程
# -------------------------------
def main():
    # 读取 Excel
    df = pd.read_excel("input.xlsx")

    # 解析 WaveDrom 模板
    templates = parse_wavedrom_adoc("input.adoc")

    # 生成 code 列
    df['code'] = df.apply(lambda row: generate_code(row, templates), axis=1)

    # 输出 Excel
    df.to_excel("output.xlsx", index=False)
    print("生成完成：output.xlsx")

if __name__ == "__main__":
    main()

