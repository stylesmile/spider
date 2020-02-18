# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/11/28 15:11
# @File    : 多语言项目质检文本入库.py
# @Date    : 2019/11/28
# @Author  : Yuwenjun
# @Desc    :


import time
import pandas as pd
import hashlib
import pathlib
import re
import pymysql
from pymongo import MongoClient


db = pymysql.connect(host='39.97.250.105', port=3307, user='root', passwd='db123456!', db='will_art')
client = MongoClient("39.97.250.105", 27015)
mongodb = client.data
# mongodb.authenticate('tasks', 'admin123456!')

mark_symbol = re.compile(r"[۔,.:;?“”‘’！＝=|()&!*@$%<>+-/'\"]+")
special_symbol = re.compile(r"[#'＋－×÷﹢﹣±＝=▣☆•，。★、😂【】《》？“”‘’！[]_`~]+")


def get_content_md5(content):
    md5_value = hashlib.md5(content.encode("utf-8")).hexdigest()
    return md5_value


def insert_mysql(dataset_name, col_name, dataset_count, duration, type, mark_type):
    print('insert mysql start')
    cusor = db.cursor()
    current_time = int(time.time() * 1000)

    try:
        sql = "SELECT dataset_count FROM `dataset` WHERE `col_name`='{}';".format(col_name)
        # 执行sql语句
        cusor.execute(sql)
        row = cusor.fetchone()
        if row:
            print("dataset已经写入该数据集，该集合应该执行更新操作非插入操作，请排查代码错误")
            exit(1)
        sql = 'INSERT INTO `dataset` (`dataset_name`,`col_name`,`dataset_count`,`duration`,`type`,`mark_type`,`status`,`created_at`,`updated_at`)' \
              ' VALUES ("{}","{}",{},{},{},{},0,{},{});'.format(dataset_name, col_name, dataset_count, duration, type,
                                                                mark_type, current_time, current_time)
        print(sql)
        cusor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except:
        print('提交mysql异常，请检查')
        # 如果发生错误则回滚
        db.rollback()


def update_mysql(col_name, dataset_count):
    print("update mysql start")
    cusor = db.cursor()
    current_time = int(time.time() * 1000)
    try:
        sql = "SELECT dataset_count FROM `dataset` WHERE `col_name`='{}';".format(col_name)
        # 执行sql语句
        cusor.execute(sql)
        row = cusor.fetchone()
        last_count = row[0]
        sql = '''UPDATE `dataset` SET `dataset_count`={}, `updated_at`={} WHERE `col_name`="{}";''' \
            .format(dataset_count + last_count, current_time, col_name)
        print(sql)
        cusor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except:
        print('提交mysql异常，请检查')
        # 如果发生错误则回滚
        db.rollback()


def create_unique_index(col_name):
    col = mongodb[col_name]
    all_index = col.index_information()
    has_md5_index = all_index.get("md5_1", False)
    has_order_index = all_index.get("order_1", False)

    if has_md5_index:
        if all_index['md5_1'].get('unique', False):  # md5为唯一索引
            pass
        else:
            col.drop_index([("md5", 1)])
            col.create_index([("md5", 1)], unique=True)  # 尝试创建唯一索引
        # return True  # True或者False表示集合是否存在
    else:
        col.create_index("md5", unique=True)  # 尝试创建唯一索引
        # return False

    if has_order_index:
        if all_index['order_1'].get('unique', False):
            pass
        else:
            col.drop_index([("oder", 1)])
            col.create_index([("order", 1)], unique=True)
    else:
        col.create_index("order", unique=True)


def get_md5_from_mongo(col_name, content_dict):
    col = mongodb[col_name]
    ret_list = list(col.find({"md5": {"$in": list(content_dict.keys())}}))
    for ret in ret_list:
        md5 = ret.get("md5")
        del content_dict[md5]
    return content_dict


def build_content_dic(order, content, origin, category):
    content_dic = dict()
    # clear_content = mark_symbol.sub("", content.replace(" ", ""))  # 去掉空格，标点符号计算md5
    md5 = get_content_md5(content)
    current_time = int(time.time() * 1000)
    content_dic['order'] = order
    content_dic['content'] = content
    content_dic['handleStatus'] = 0  # 0代表未使用，1代表使用
    content_dic['origin'] = origin
    content_dic['category'] = category
    content_dic['md5'] = md5
    content_dic['use'] = 0  # 0代表初始状态，1是txt，2是json，3是Excel，4是TXT和json
    content_dic['createAt'] = current_time
    # ret = get_md5_from_mongo(col_name, md5)
    # return content_dic if not ret else None
    return content_dic


def get_col_last_order(col_name):
    col = mongodb[col_name]
    if col.count() > 0:
        ret = col.find({}).sort([("order", -1)]).limit(1)
        return ret[0].get("order") + 1
    else:
        return 1


def choose_colName_and_datasetName(language):
    names = {
        "荷兰": "col_dutch_text",
        "瑞典": "col_swedish_text",
        "丹麦": "col_danish_text",
        "泰米尔": "col_tamil_text",
        "老挝": "col_laotian_text",
        "波斯": "col_farsi_text",
        "挪威": "col_norwegian_text",
        "尼泊尔": "col_nepali_text",
        "爪哇": "col_javanese_text",
        "马拉地": "col_marathi_text",
        "巽他": "col_sundanese_text",
        "泰卢固": "col_telugu_text",
        "乌尔都": "col_urdu_text",
        "新蒙": "col_new_mongolian_text",
        "土库曼": "col_turkmen_text",
        "普什图": "col_pashto_text",
        "豪萨": "col_hausa_text",
        "乌兹别克": "col_uzbek_text",
        "哈萨克": "col_kazakh_text",
        "塔吉克": "col_tajik_text"
    }
    res = names.get(language)
    if not res:
        print("未找到对应的语言预置信息，请检查输入语言类型是否正确")
        exit(1)
    return res


def main(input_path, language, header, sheet_name):
    print("--- script start ---")
    header = 0 if header else None
    if sheet_name:
        df = pd.read_excel(input_path, header=header, encoding="utf-8", sheet_name=sheet_name)
    else:
        df = pd.read_excel(input_path, header=header, encoding="utf-8")
    print("--- success read excel --- ")

    df = df.drop_duplicates()

    col_name = choose_colName_and_datasetName(language)

    print("--- start write to mongo ---")
    create_unique_index(col_name)  # 给集合中的md5字段建立唯一索引

    data_dic = dict()
    count = 0
    order = get_col_last_order(col_name)  # 获取当前集合最后一条数据的order
    origin = pathlib.Path(input_path).name.split(".")[0]
    category = 0
    col_index = "content" if header else 0
    for row in df.iterrows():
        content = row[1][col_index].strip().replace("\n", " ").replace("\r\n", " ")
        # order = row[1][1]
        # content = special_symbol.sub("", content)  # 去掉特殊符号
        if not content:
            continue
        # origin = row[1]['origin']
        # category = row[1]['category']
        content_dict = build_content_dic(order, content, origin, category)

        if not content_dict:
            continue
        order += 1

        data_dic[content_dict.get("md5")] = content_dict
        if len(data_dic.keys()) == 200000:
            _data_dic = get_md5_from_mongo(col_name, data_dic)
            if len(_data_dic.keys()) == 0:
                print("--- 本次待入库文本数据库全部存在 ---")
                exit(1)
            res = mongodb[col_name].insert_many([value for value in _data_dic.values()], ordered=False)
            count += len(_data_dic.keys())
            print("已经向MongoDB中写入了%s条数据" % len(res.inserted_ids))
            data_dic.clear()
            del _data_dic
        # print(content_dict)
    _data_dic = get_md5_from_mongo(col_name, data_dic)
    count += len(_data_dic.keys())
    if len(_data_dic.keys()) == 0:
        print("--- 本次待入库文本数据库全部存在 ---")
        exit(1)
    res = mongodb[col_name].insert_many([value for value in data_dic.values()], ordered=False)
    print("已经向MongoDB中写入了%s条数据" % len(res.inserted_ids))

    del data_dic
    del _data_dic
    print("--- script end 总数据>>>{}条,去重后插入了>>>{}条数据 ---".format(df.count()[0], count))


if __name__ == '__main__':
    input_path = input("请输入Excel文件路径：")
    language = input("请输入Excel对应的语言，如丹麦、荷兰等：")
    header = input("Excel是否存在表头，输入1有表头，任意其它按键无表头：")
    header = int(header) if header == "1" else 0
    sheet_name = input("请输入Excel的表名，不输入默认第一个：")
    sheet_name = sheet_name if sheet_name else None
    main(input_path, language, header, sheet_name)
