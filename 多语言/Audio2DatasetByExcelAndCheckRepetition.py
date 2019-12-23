
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/10/15 11:59
# @File    : Audio2DatasetByExcelAndCheckRepetition.py
# @Date    : 2019-10-15
# @Author  : Yuwenjun
# @Desc    :
import time
import os
import openpyxl
import pymysql
from pymongo import MongoClient


class Audio2DatasetByExcelAndCheckRepetition(object):
    def __init__(self, db, mongodb, colName, datasetName, types, markType, excelPath, textPath):
        self.db = db
        self.mongodb = mongodb
        self.colName = colName
        self.datasetName = datasetName
        self.types = types
        self.markType = markType
        self.excelPath = excelPath
        self.textPath = textPath

    def readwb(self, file_path, sheetname="Mysheet"):
        """
        读取Excel数据，存储到列表中
        :param sheetname: 表名
        :return:
        """
        wb = openpyxl.load_workbook(filename=file_path, read_only=True)
        if (sheetname == ""):
            ws = wb.active
        else:
            ws = wb[sheetname]
        data = []
        # regions= ws.cell(row=1,column=2)
        for row in ws.rows:
            list = []
            for cell in row:
                aa = str(cell.value)
                if (aa == ""):
                    aa = "1"
                list.append(aa)
            data.append(list)
        print(file_path + "-" + sheetname + "- 已成功读取")
        wb.close()
        return data

    def insert_mongo(self, label_data):
        print('insert mongo start')
        col = mongodb[self.colName]
        print(label_data)
        # col.insert_one(label_data)
        col.insert_many(label_data)

    def insert_duplicate_checking(self, dataList):
        """
        数据重复核查OK后，将导入数据插入到查重表中
        :param dataList:
        :return:
        """
        print("--- 开始向查重表中写入数据 ---")
        col_list = list()
        current_time = int(time.time() * 1000)
        datas = dataList[1:] if self.types == 1 and self.markType == 9 else dataList
        for data in datas:
            insert = dict()
            if self.types == 0:
                insert['url'] = data[2]
                insert['name'] = data[0]
                insert['md5'] = data[3]
                insert['content'] = ""
            if self.types == 1:
                insert['md5'] = ""
                if self.markType == 9:
                    insert['url'] = data[dataList[0].index("ID")]
                    insert['name'] = data[dataList[0].index("游戏")]
                    insert['content'] = data[dataList[0].index("内容")]
                if self.markType == 10:
                    # 英语文本可以重复，不写入查重表中
                    return
                    insert['url'] = ""
                    insert['name'] = ""
                    insert['content'] = data
            insert['type'] = self.types
            insert['markType'] = self.markType
            insert['property'] = {
                'datasetName': self.datasetName,
                'colName': self.colName
            }
            insert['isDelete'] = 0
            insert['isDeliver'] = 0
            insert['createdAt'] = current_time
            insert['updateAt'] = current_time
            col_list.append(insert)
        self.mongodb['duplicate_checking'].insert_many(col_list)
        print("--- 查重表数据写入完毕 ---")

    def insert_mysql(self, dataset_count, duration):
        print('insert mysql start')
        cusor = db.cursor()
        current_time = int(time.time() * 1000)
        sql = 'INSERT INTO `dataset` (`dataset_name`,`col_name`,`dataset_count`,`duration`,`type`,`mark_type`,`status`,`created_at`,`updated_at`)' \
              ' VALUES ("{}","{}",{},{},{},{},0,{},{});'.format(self.datasetName, self.colName, dataset_count, duration, self.types,
                                                                self.markType, current_time, current_time)
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

    def get_audio(self, dataList):
        # url labelStatus handleStatus isValid createAt order validTime
        current_time = time.time() * 1000
        order = 1
        total_duration = 0
        label_list = list()
        datas = dataList[1:] if self.types == 1 and self.markType == 9 else dataList
        if self.markType == 5:
            textFileName = [fileName for fileName in os.listdir(self.textPath) if fileName.endswith(".xlsx")]
            if len(datas) != len(textFileName):
                print("Excel中的音频数量和文本语料路径中获取的Excel数量不一致")
        for data in datas:
            if len(data) < 1:
                print('excel数据有误，请检查')
                exit(1)
            label_data = dict()
            label_data['labelStatus'] = 0
            label_data['handleStatus'] = 0
            label_data['isValid'] = 0
            label_data['source'] = 1
            label_data['order'] = order
            label_data['createAt'] = current_time
            if self.types == 0:
                label_data['url'] = data[2]
                duration = float(data[1])
                if self.markType == 5:  # 切分校对写入文本
                    audio_name = data[0].split(".")[0] + ".xlsx"
                    text_excel_path = os.path.join(self.textPath, audio_name)
                    contents = self.readwb(text_excel_path)
                    label_content = {"labelContentList": []}

                    for content in contents:
                        if not content[0] or content[0] == 'None':
                            break
                        label_content["labelContentList"].append({"content": content[0].strip()})
                    label_data['labelContent'] = label_content
                label_data['validTime'] = duration
                label_data['totalTime'] = duration
                total_duration += duration
            if self.types == 1:
                if self.markType == 9:
                    label_data['commentId'] = data[dataList[0].index("ID")]
                    label_data['url'] = data[dataList[0].index("游戏")]
                    label_data['content'] = data[dataList[0].index("内容")].replace("<", "(").replace(">", ")")
                if self.markType == 10:
                    label_data['content'] = data[0].replace("$", "")
                    label_data['url'] = order
            label_list.append(label_data)
            order += 1
        self.insert_mongo(label_list)
        self.insert_mysql(order - 1, total_duration)

    def check_repetition(self, datas):
        """
        数据写入前进行核查
        :param datas: Excel数据
        :return:
        """
        # 检查数据集是否重复
        print("--- 开始检查数据是否重复 ---")
        if self.mongodb[self.colName].count():
            print("colName已存在，请重新输入")
            exit(1)
        if (self.types == 0 and len(datas[0]) < 4) or (self.types == 1 and len(datas[0]) > 3):
            print("数据类型和文件不一致，请核查导入数据是否为音频类型")
            exit(1)
        # 数据查重通过后，将新数据写入到查重集合中
        if self.types == 0:
            # 输入数据去重
            data_tmp = set([data[3] for data in datas])
            if len(data_tmp) != len(datas):
                print("Excel中含有重复数据，请去重后再创建任务")
                exit(1)
            for data in datas:
                md5 = data[3]
                url = data[2]
                name = data[0]
                md5_ret = self.mongodb['duplicate_checking'].find({'md5': md5}).count()
                url_name_ret = self.mongodb['duplicate_checking'].find({"$or": [
                    {"url": url},
                    {"name": name}
                ]}).count()
                if md5_ret > 0:
                    print("音频>>>{}<<<文件指纹重复".format(str(name)))
                    exit(1)
                if url_name_ret > 0:
                    print("音频>>>{}<<<文件名或者url重复".format(str(name)))
                    exit(1)
        elif self.types == 1:
            if self.markType == 9:
                i = datas[0].index("ID")
                data_tmp = set([data[i] for data in datas[1:]])
                if len(data_tmp) != len(datas) - 1:
                    print("Excel中含有重复数据，请去重后再创建任务")
                    exit(1)
                for data in datas[1:]:
                    _id = data[i]
                    ret = self.mongodb['duplicate_checking'].find({"url": _id}).count()
                    if ret > 0:
                        print("评论id>>>{}<<<在数据库中重复".format(str(_id)))
                        exit(1)
            elif self.markType == 10:
                # 英语不检查重复
                pass
                # for data in datas:
                #     ret = self.mongodb['duplicate_checking'].find({"content": data}).count()
                #     if ret > 0:
                #         print("英语文本>>>{}<<<重复导入".format(str(data)))
                #         exit(1)
        self.insert_duplicate_checking(datas)
        print("--- 数据查重完毕 ---")

    def run(self):
        print("--- script start ---")
        s = time.time()
        dataList = self.readwb(self.excelPath)
        self.check_repetition(dataList)
        self.get_audio(dataList)
        e = time.time()
        print("\n")
        print("--- script end 耗时>>> %s秒---", e - s)


if __name__ == '__main__':
    # db = pymysql.connect(host='192.168.0.37', user='will_art', passwd='jFHKm2i4rg4WqpMz', db='will_art')
    # client = MongoClient("192.168.0.37", 27017)

    db = pymysql.connect(host='39.97.250.105', user='will_art', passwd='db123456!', db='will_art')
    client = MongoClient("39.97.250.105", 27016)
    mongodb = client.tasks
    mongodb.authenticate('tasks', 'admin123456!')4
    config = {
        "db": "",
        "mongodb": "",
        "colName": "",
        "datasetName": "",
        "types": "",
        "markType": "",
        "excelPath": "",
        "textPath": "",
    }
    excel_path = input("请输入上个步骤生成的excel文件地址：")
    col_name = input("请输入collection名称，比如col_test01：")
    dataset_name = input("请输入数据集展示名称，比如测试数据集01：")
    types = int(input("请输入数据类型，0：语音，1：文本，2：图片："))
    mark_type = int(input("请输入数据标注类型，0：ASR，1：客服语音，2：文本扩写, 3:时间轴， 4:文本问答，5:切分校对，6:粤语语音模板，8:粤语语音模板V2.0，9:游戏情感标注,\n"
                          "10：英语标注，11：问答模板，12：英语标注2 >>>\n"))
    if mark_type == 5:
        text_path = input("请输入文本语料路径(切分校对模板专用:需要保证Excel名字和音频名一致),如F:\\test2：")
        if os.path.isdir(text_path):
            config['textPath'] = text_path
        else:
            print("请输入有效的文本语料路径")
            exit(1)
    if all([excel_path, col_name, dataset_name, str(types), mark_type]):
        config["db"] = db
        config["mongodb"] = mongodb
        if not col_name.startswith("col_"):
            print("colName命名错误")
            exit(1)
        if not types in [0, 1, 2]:
            print("数据类型输入错误")
            exit(1)
        if not mark_type in [i for i in range(11)]:
            print("标注数据错误")
            exit(1)
        config["colName"] = col_name.strip()
        config["datasetName"] = dataset_name.strip()
        config["types"] = types
        config["markType"] = mark_type
        config["excelPath"] = excel_path.strip()
        manager = Audio2DatasetByExcelAndCheckRepetition(**config)
        manager.run()
    else:
        print("输入数据不能为空")
        exit(1)
