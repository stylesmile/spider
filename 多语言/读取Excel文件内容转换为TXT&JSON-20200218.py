# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/12/17 11:02
# @File    : 读取Excel文件内容转换为TXT.py
# @Date    : 2019/12/17
# @Author  : Yuwenjun
# @Desc    : 读取Excel内容写入TXT中
import os
from functools import reduce

import pandas as pd
# import numpy as np
import math
import json
import codecs
import pathlib


class Excel2Txt(object):
    def __init__(self, input_path: str, col: str, header: int, sheet_name: str, split_count: int):
        self.input_path = input_path
        self.col = col
        self.header = header
        self.sheet_name = sheet_name
        self.col_tag = False
        self.split_count = split_count

    def read_excel(self, path):
        xls_data = pd.ExcelFile(path)
        df = None
        if self.sheet_name:
            sheet_names = [self.sheet_name]
        else:
            sheet_names = xls_data.sheet_names
        for sheet_name in sheet_names:
            _df = xls_data.parse(sheet_name=sheet_name, header=self.header, encoding='utf-8')
            df = pd.concat([df, _df], ignore_index=True)
        return df

    def switch_order(self, length, order):
        return {
            1: lambda x: "000" + str(order),
            2: lambda x: "00" + str(order),
            3: lambda x: "0" + str(order),
            4: lambda x: str(order)
        }[length](order)

    def write_2_txt(self, df, output_path):
        with codecs.open(output_path, "w", encoding="utf-8") as f:
            if self.col.isdigit():
                col_index = int(self.col)
            else:
                if self.header and self.col:
                    col_index = self.col
                else:
                    col_index = 0
            for row in df.iterrows():
                content = row[1][col_index].strip().replace("\n", " ").replace("\r\n", " ")
                f.write(content + "\n")
                # f.write(reduce(lambda x, y: str(x)+str(y), map(ord, content)) + "\n")
                # f.write('%d'*len(s) % tuple(map(ord, content)) + "\n")
                # f.write(''.join(str(ord(c)) for c in content) + "\n")
                # ascii_str = np.fromstring(content, dtype=np.uint8).tostring()
                # print(ascii_str)
                # f.write(ascii_str.decode().encode("ascii") + "\n")

    def write_2_json(self, df, output_path):
        print(f"当前处理的文件是>>>{output_path}")
        path = pathlib.Path(output_path)
        json_dic = dict()
        json_dic['taskName'] = path.name.split(".")[0]
        json_dic['datasets'] = list()
        order = 1
        with codecs.open(output_path, "w", encoding="utf-8") as f:
            for row in df.iterrows():
                content = row[1][0].strip().replace("\n", " ").replace("\r\n", " ")
                # order = row[1][1]
                json_dic['datasets'].append({
                    "content": content,
                    "isSave": False,
                    "order": self.switch_order(len(str(order)), order),
                    "transContent": content
                })
                order += 1
            json.dump(json_dic, f)

    def run(self):
        print("--- script start ---")
        df = None
        for name in os.listdir(self.input_path):
            if not name.endswith(".xlsx"):
                continue
            excel_path = os.path.join(self.input_path, name)
            _df = self.read_excel(excel_path)
            # df = df.drop_duplicates().dropna()
            df = pd.concat([df, _df], ignore_index=True)
            count = df.count()[0]

            # tmp = -14
            single_txt_count = math.floor(count / self.split_count)
            for i in range(0, single_txt_count):
                _df = df[i * self.split_count:(i + 1) * self.split_count]
                obj_path = pathlib.Path(excel_path)
                parent = obj_path.parent
                name = obj_path.name.split(".")[0]
                # if i > 3:
                #     tmp = 3
                # order = str(i + 22)
                # print(order)
                # s_order = order if len(order) > 2 else "0" + order
                # print(s_order)
                # if tmp != -14:
                # name = "Urdu-NJ-0{}".format(s_order)
                # else:
                #     name = "Urdu-S-0{}".format(s_order)
                txt_path = os.path.join(parent, name + ".txt")
                txt_path2 = os.path.join(parent, name + ".json")
            self.write_2_txt(_df, txt_path)
            self.write_2_json(_df, txt_path2)
        print("--- script end ---")


if __name__ == '__main__':
    input_path = input("请输入Excel文件路径：")
    col_name = input("请输入提取文本的列名或者列数，A列对应0，默认为0：")
    header = input("请输入header，0或者1：")
    sheet_name = input("请输入sheet_name名：")
    split_count = input("请输入切分数量，默认1000句一个txt：")
    header = 0 if header else None
    split_count = int(split_count) if split_count else 1100
    obj = Excel2Txt(input_path, col_name, header, sheet_name, split_count)
    obj.run()
