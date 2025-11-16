wildcard bins g = {32'b1111???};
    group_info = [
        (["V", "X", "I"], {"V": "OPIVV", "X": "OPIVX", "I": "OPIVI"}, 5),  # 第一组
        (["V", "X"], {"V": "OPMVV", "X": "OPMVX"}, 4),                     # 第二组
        (["V", "F"], {"V": "OPFVV", "F": "OPFVF"}, 4),                     # 第三组
    ]
