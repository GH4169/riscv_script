#!/usr/bin/env python3
# coding=utf-8

import sys
import re
import os
import pandas as pd

def gen_funct6_funct3_inst(input_file, output_file="output.xlsx"):# {{{
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

def parse_vs1_vs2_adoc(adoc_file):# {{{
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

def parse_funct6_funct3_inst_xlsx(excel_file):# {{{
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

def merge_vs1_vs2_doc_and_funct6_funct3_inst_xlsx(adoc_entries, opcode_map):# {{{
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

def gen_vs1_vs2_inst(adoc_file, excel_file, output_excel="result.xlsx"):# {{{
    adoc_entries = parse_vs1_vs2_adoc(adoc_file)
    opcode_map = parse_funct6_funct3_inst_xlsx(excel_file)
    merged_results = merge_vs1_vs2_doc_and_funct6_funct3_inst_xlsx(adoc_entries, opcode_map)

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


# 解析 WaveDrom 模板
def parse_wavedrom_adoc(file_path):# {{{
    templates = []
    with open(file_path, "r") as f:
        data = f.read()
    # 去掉 ```wavedrom 和 ```
    data = re.sub(r'```wavedrom', '', data)
    data = data.replace('```', '')

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
                name = name.strip("'\]\"")
                name = re.sub(r"[\:\/\[\]\s]+", "_", name)
                # name = re.sub(r"_+", "_", name)
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

# 根据 Excel 行选择模板
def select_template(templates, funct3_val):# {{{
    for t in templates:
        if 'attr' in t["reg"][0] and t["reg"][0].get("attr") == funct3_val:
            return t["reg"]
    return None# }}}

def gen_single_inst_code(template, row):# {{{
    """
    根据 WaveDrom template 和 Excel 行，生成 32bit 指令编码字符串
    - template: [{'bits': 7, 'name': '0x57'}, {'bits': 5, 'name': 'vd'}, ...]
    - row: Excel 一行，包含字段值
    """
    code_bits = []
    
    for f in template:
        name = f.get("name")
        width = f.get("bits", 0)
        
        # opcode / 常数字段，例如 0x57
        if name.startswith("0x"):
            val = bin(int(name, 16))[2:].zfill(width)
            code_bits.append(val)
            continue

        # 如果 name 本身是数字
        try:
            val_int = int(name, 0)  # 支持 10 进制或 0x 十六进制
            val_bin = bin(val_int)[2:].zfill(width)
            code_bits.append(val_bin)
            continue
        except:
            pass  # 非数字字段，继续处理 Excel 列匹配
        # 对应 Excel 列
        col_name = name.lower()  # 小写匹配
        val = row.get(col_name)
        
        if pd.isna(val) or str(val).strip() == "":
            # Excel 中没有值，用 ? 占位
            val_bin = "?" * width
        else:
            # Excel 本身就是二进制字符串，去掉空格并补齐
            val_str = str(val).strip()
            val_bin = val_str.zfill(width)

        code_bits.append(val_bin)

    # 拼成 SystemVerilog 风格
    code_bits = code_bits[::-1]  # 反转列表
    return "32'b" + "_".join(code_bits)# }}}

def gen_all_inst_code_fcov(template_file, input_excel, output_excel, output_fcov):# {{{
    templates = parse_wavedrom_adoc(template_file)
    df = pd.read_excel(input_excel, dtype=str)

    codes = []
    with open(output_fcov, "w") as f_fcov:
        for _, row in df.iterrows():
            funct3 = row.get("funct3")
            tmpl = select_template(templates, funct3)
            if tmpl:
                code = gen_single_inst_code(tmpl, row)
            else:
                raise ValueError(f"No matching template found for funct3={funct3}")
            
            codes.append(code)

            # 写入 fcov 文件
            assembly = row.get("assembly", "").strip()
            f_fcov.write(f"wildcard {assembly} = {{{code}}};\n")

    df["code"] = codes
    df.to_excel(output_excel, index=False)
    print("generated: ", output_excel)
    print("generated: ", output_fcov)# }}}

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} funct6_funct3.adoc vs1_vs2.adoc op_format.adoc")
        sys.exit(1)

    os.makedirs("generated_v_inst", exist_ok=True)

    funct6_funct3_adoc = sys.argv[1]
    funct6_funct3_inst_xlsx = os.path.join("generated_v_inst", "funct6_funct3_inst.xlsx")
    gen_funct6_funct3_inst(funct6_funct3_adoc, funct6_funct3_inst_xlsx)


    vs1_vs2_adoc = sys.argv[2]
    vs1_vs2_inst_xlsx = os.path.join("generated_v_inst", "vs1_vs2_inst.xlsx")
    gen_vs1_vs2_inst(vs1_vs2_adoc, funct6_funct3_inst_xlsx, vs1_vs2_inst_xlsx)

    all_v_inst_xlsx = os.path.join("generated_v_inst", "all_v_inst.xlsx")
    merge_all_inst(funct6_funct3_inst_xlsx, vs1_vs2_inst_xlsx, all_v_inst_xlsx)


    op_format_adoc = sys.argv[3];
    all_v_inst_xlsx_code_xlsx = os.path.join("generated_v_inst", "all_v_inst_code.xlsx");
    all_v_inst_fcov = os.path.join("generated_v_inst", "all_v_inst_fcov.sv");
    gen_all_inst_code_fcov(op_format_adoc, all_v_inst_xlsx, all_v_inst_xlsx_code_xlsx, all_v_inst_fcov)
