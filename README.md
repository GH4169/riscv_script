# rsicv_script

RISC-V 相关脚本仓库，目前只有gen_v_inst.py用于生成RISC-V vector指令编码、功能覆盖率，后续会扩展更多 RISC-V 脚本。

## 仓库结构
```
rsicv_script/
├── gen_v_inst_code/
│   └── gen_v_inst.py # 生成向量指令编码、功能覆盖率的脚本
└── README.md
```

## gen_v_inst.py
生成向量指令编码和功能覆盖率的脚本，输入来自以下文件（只处理运算指令）：  

- [inst-table.adoc](https://github.com/riscvarchive/riscv-v-spec/blob/master/inst-table.adoc)  
- [valu-format.adoc](https://github.com/riscvarchive/riscv-v-spec/blob/master/valu-format.adoc)  

**注意事项**：  
- 只生成运算指令编码和功能覆盖率
-  `vm bit` 未处理
- 特殊编码暂未处理

**用法：**

```
cd gen_v_inst_code
./gen_v_inst.py funct6_funct3.adoc vs1_vs2.adoc op_format.adoc
```
