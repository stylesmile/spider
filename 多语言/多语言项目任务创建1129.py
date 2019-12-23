# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/11/28 15:11
# @File    : 多语言项目任务创建.py
# @Date    : 2019/11/28
# @Author  : Yuwenjun
# @Desc    :


import time
import pandas as pd
import hashlib
import re
import pymysql
from pymongo import MongoClient


db = pymysql.connect(host='39.97.250.105', user='root', passwd='db123456!', db='will_art', port=3305)
client = MongoClient("39.97.250.105", 27017)
mongodb = client.tasks
mongodb.authenticate('tasks', '05KjjkCTS2lebEPC')

mark_symbol = re.compile(r"[۔,.:;?|()&!*@$%<>+-/'\"]")
special_symbol = re.compile(r"[#'＋－×÷﹢﹣±＝=▣☆•，。★、😂【】《》？“”‘’！[]_`{|\u4e00-\u9fa5}~]+")


def get_content_md5(content):
    md5_value = hashlib.md5(content.encode("utf-8")).hexdigest()
    return md5_value


def insert_mysql(dataset_name, col_name, dataset_count, duration, type, mark_type):
    print('insert mysql start')
    cusor = db.cursor()
    current_time = int(time.time() * 1000)
    sql = 'INSERT INTO `dataset` (`dataset_name`,`col_name`,`dataset_count`,`duration`,`type`,`mark_type`,`status`,`created_at`,`updated_at`)' \
          ' VALUES ("{}","{}",{},{},{},{},0,{},{});'.format(dataset_name, col_name, dataset_count, duration, type,
                                                            mark_type, current_time, current_time)
    print(sql)
    try:
        # 执行sql语句
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
    has_md5_index = all_index.get("md5", False)
    if has_md5_index:
        if all_index['md5'].get('unique', False):  # md5为唯一索引
            pass
        else:
            col.drop_index([("md5", 1)])
            col.create_index([("md5", 1)], unique=True)  # 尝试创建唯一索引
    else:
        col.create_index([("md5", 1)], unique=True)  # 尝试创建唯一索引


def build_content_dic(order, content, origin, category):
    content_dic = dict()
    clear_content = mark_symbol.sub("", content.replace(" ", ""))  # 去掉空格，标点符号计算md5
    md5 = get_content_md5(clear_content)
    current_time = int(time.time() * 1000)
    content_dic['order'] = order
    content_dic['content'] = content
    content_dic['labelStatus'] = 0
    content_dic['handleStatus'] = 0
    content_dic['origin'] = origin
    content_dic['source'] = 1
    content_dic['category'] = category
    content_dic['md5'] = md5
    content_dic['createAt'] = current_time
    return content_dic


def get_col_last_order(col_name):
    col = mongodb[col_name]
    if col.count() > 0:
        ret = col.find({}).sort([("_id", -1)]).limit(1)
        return ret.get("order") + 1
    else:
        return 1


def main(input_path, col_name, dataset_name, sheet_name=None):
    print("--- script start ---")
    if sheet_name:
        df = pd.read_excel(input_path, encoding="utf-8", sheet_name=sheet_name)
    else:
        df = pd.read_excel(input_path, encoding="utf-8")
    print("--- success read excel --- ")

    df = df.drop_duplicates(subset="content").dropna()

    print("--- start write to mongo ---")
    create_unique_index(col_name)  # 给集合中的md5字段建立唯一索引
    data_dic = dict()
    count = 0
    order = get_col_last_order(col_name)  # 获取当前集合最后一条数据的order
    for row in df.iterrows():
        content = row[1]['content'].strip()
        content = special_symbol.sub("", content)  # 去掉特殊符号
        if not content:
            continue
        origin = row[1]['origin']
        category = row[1]['category']
        content_dict = build_content_dic(order, content, origin, category)

        if not content_dict:
            continue
        order += 1

        data_dic[content_dict.get("md5")] = content_dict
        if len(data_dic.keys()) == 5000:
            count += 5000
            mongodb[col_name].insert_many([value for value in data_dic.values()], ordered=False)
            data_dic.clear()
        print(content_dict)
    count += len(data_dic.keys())
    mongodb[col_name].insert_many([value for value in data_dic.values()], ordered=False)
    insert_mysql(dataset_name, col_name, count, 0, 1, 5)
    data_dic.clear()
    print("--- script end 插入了>>{}<<条数据---".format(count))


if __name__ == '__main__':
    input_path = input("请输入Excel文件路径：")
    col_name = input("请输入数据集名称：")
    dataset_name = input("请输入数据集中文名：")
    main(input_path, col_name, dataset_name)