# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/12/31 15:50
# @File    : Excel多个Sheet合并.py
# @Date    : 2019/12/31
# @Author  : Yuwenjun
# @Desc    : 合并Excel多个sheet
import time

import pandas as pd
import os


class MergeExcel:
    def __init__(self, header, col, input_path):
        self.input_path = input_path
        self.header = header
        self.col = col
        self.col_tag = False

    def read_excel(self, path):
        df = None
        xls_data = pd.ExcelFile(path)
        for sheet_name in xls_data.sheet_names:
            _df = xls_data.parse(sheet_name=sheet_name, header=self.header, encoding='utf-8')
            df = pd.concat([df, _df], ignore_index=True)
        if self.col is None:
            return df.drop_duplicates()
        elif not self.col_tag:
            return df[[int(index) for index in self.col.split(",")]].dropna().drop_duplicates()
        else:
            return df[[index for index in self.col.split(",")]].dropna().drop_duplicates()

    def merge_excel(self, names):
        df = None
        if names:
            for name in names:
                print("当前正在处理的Excel文件是{}".format(name))
                path = os.path.join(self.input_path, name)
                _df = self.read_excel(path)
                excel_name = [name] * _df.count()[0]
                _df.insert(1, "1", excel_name)
                df = pd.concat([df, _df], ignore_index=True)
        else:
            df = self.read_excel(self.input_path)
        return df.drop_duplicates().dropna()

    def run(self):
        excel_names = None
        if os.path.isdir(self.input_path):
            excel_names = [name for name in os.listdir(self.input_path) if name.endswith((".xls", ".xlsx"))]
        df = self.merge_excel(excel_names)

        prefix = time.strftime('%Y%m%d%H')
        dir_name = os.path.split(self.input_path)
        if excel_names:
            output_path = os.path.join(self.input_path, "{}_{}_合并_{}句.xlsx".format(dir_name[1], prefix, df.count()[0]))
        else:
            output_path = self.input_path.split(".")[0] + "_{}_合并_{}句.xlsx".format(prefix, df.count()[0])
        print(output_path)
        df.to_excel(output_path, index=False, header=False)


if __name__ == '__main__':
    header = input("请确认Excel是否包含表头，0无表头，其它有表头，默认为0：")
    col = input("请指定Excel各sheet需要合并的列，0代表A列，依此类推，默认合并全部：")
    input_path = input("请输入Excel文件夹路径或者单个文件地址：")
    if not input_path:
        print("请确认Excel的文件夹存放路径是否输入完整")
        exit(1)
    config = {
        "header": None if not header else header,
        "col": None if not col else col,
        "input_path": input_path
    }
    main = MergeExcel(**config)
    main.run()
