#!/usr/bin/env python3
# coding=utf-8

import re
import pandas as pd
import sys

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
    print(templates)
    return templates# }}}

# 根据 Excel 行选择模板
def select_template(templates, funct3_val):# {{{
    for t in templates:
        if 'attr' in t["reg"][0] and t["reg"][0].get("attr") == funct3_val:
            return t["reg"]
    return None# }}}


def generate_code(template, row):# {{{
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

def process_excel(template_file, input_excel, output_excel, output_fcov):# {{{
    templates = parse_wavedrom_adoc(template_file)
    df = pd.read_excel(input_excel, dtype=str)

    codes = []
    with open(output_fcov, "w") as f_fcov:
        for _, row in df.iterrows():
            funct3 = row.get("funct3")
            tmpl = select_template(templates, funct3)
            if tmpl:
                code = generate_code(tmpl, row)
            else:
                raise ValueError(f"No matching template found for funct3={funct3}")
            
            codes.append(code)

            # 写入 fcov 文件
            assembly = row.get("assembly", "").strip()
            f_fcov.write(f"wildcard {assembly} = {{{code}}};\n")

    df["code"] = codes
    df.to_excel(output_excel, index=False)
    print("已生成：", output_excel)
    print("已生成：", output_fcov)# }}}


# 执行入口
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} op_format.adoc all_v_inst.xlsx")
        sys.exit(1)
    process_excel(sys.argv[1], sys.argv[2], "all_v_inst_code.xlsx", "all_v_inst_fcov.sv")
