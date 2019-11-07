# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/10/21 10:15
# @File    : 荷兰网站爬虫.py
# @Date    : 2019/10/21
# @Author  : chenye
# @Desc    :

# request库官方文档
# https://requests.kennethreitz.org//zh_CN/latest/user/quickstart.html

import requests  # request库，根据URL发起请求获取响应
from lxml import etree  # xpath 解析HTML
from queue import Queue  # 队列，保证每个子线程任务唯一
from multiprocessing.dummy import Pool  # 线程池
from retrying import retry
import time  # 时间模块


class NewsSpider:
    def __init__(self):
        """分页列表的地址"""
        self.url_temp = "https://www.ted.com/talks?language=da&sort=newest&page={}"  # 用于拼接的URL地址，加大括号是为了format赋值
        self.url_temp_header = "https://www.ted.com/talks?language=da&sort=newest"  # 首页URL地址
        self.host_header = "https://www.ted.com"  # 相当于host，用于拼接全详情也URL
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"}
        self.queue = Queue()  # 实例化一个队列
        self.pool = Pool(8)  # 实例化一个线程池，最大为20
        self.cookies = {"_ga": "GA1.2.1926840070.1572493439",
                        "_gid": "GA1.2.1938278653.1572493439",
                        "cookieconsent_status": "dismiss"}  # 针对一些有反爬措施的网站，带上cookie
        self.is_running = True  # 回调标志位
        self.total_requests_num = 0  # 待完成任务数量
        self.total_response_num = 0  # 完成任务数量
        self.filename = "ted丹麦0-339.txt"  # 文件名
        self.startNumber = 0  # 开始页数
        self.endNumber = 339  # 结束页数

    def parse_url_list(self, html):
        # 解析列表页HTML，获取详情页URL列表
        html = etree.HTML(html)
        url_list = html.xpath("//[@class='media__image media__image--thumb talk-link__image']/a/@href")
        return url_list

    def get_url_list(self):
        # 构造URL列表页网址，拼接补全详情页URL，并加入到队列
        for i in range(self.startNumber, self.endNumber):  # range为左闭右开，表示从1到100循环，i代表每次循环的值
            try:
                if i == 1:  # 针对首页不带后缀的，使用头URL
                    html = self.parse_url(self.url_temp_header)
                else:
                    html = self.parse_url(self.url_temp.format(i))
                # 获取详情页URL，并将详情页URL加入到任务队列
                url_list = self.parse_url_list(html)
                for url in url_list:
                    # url = self.host_header + url  # 如果详情页URL不完整，手动补全
                    url = url  # 如果详情页URL不完整，手动补全
                    print(url)
                    self.queue.put(url)  # 队列任务加1
                    self.total_requests_num += 1  # 数量加1
            except Exception as e:
                print(e)

    @retry(stop_max_attempt_number=3)
    def parse_url(self, url):
        time.sleep(0.5)
        # 发送请求，获取响应
        response = requests.get(url, headers=self.headers)
        # 需要session的话，注释掉上面的代码，使用下面代码
        # session = requests.session()
        # response = session.get(url, headers=headers)
        return response.content.decode()  # conten方法解析不出内容的话，换成text

    @staticmethod
    def split_content(content):
        """
        根据标点符号切割文本句子
        :param content: 原始字符串
        :return: 切割后的文本
        """
        content_list = list()
        e = 0
        for k, v in enumerate(content):
            if k == 0:
                if v == ".":
                    e = 1
            elif k < len(content) - 1:
                if v == ".":
                    if content[k - 1] != "." and content[k + 1] != ".":
                        if content[k - 1].isdecimal() and content[k + 1].isdecimal():
                            continue
                        if content[k - 1].isalpha() and content[k + 1].isalpha():
                            continue
                        content_list.append(content[e:k].strip())
                        e = k + 1
                if v == "?":
                    if content[k - 1] != "?" and content[k + 1] != "?" and content[k + 1] != ")":
                        content_list.append(content[e:k + 1].strip())
                        e = k + 1
                if v == ";" and len(content) > 200:
                    content_list.append(content[e:k + 1].strip())
                    e = k + 1
                if v == "!" and len(content) > 200:
                    content_list.append(content[e:k + 1].strip())
                    e = k + 1
            else:
                if v == ".":
                    content_list.append(content[e:-1].strip())
                else:
                    content_list.append(content[e:].strip())
        return content_list

    # 获取html的内容
    def get_content_list(self, html_str):
        # 提取详情也的文本内容，返回文本列表
        html = etree.HTML(html_str)
        # contents = html.xpath("//div[@id='abody']/p/text()")
        contents = html.xpath("//div[@class='layout-row']/div[@class='main']/div[@class='text']/text()")

        content_list = []
        for content in contents:
            if content.strip():
                content_merge_list = self.split_content(
                    content.replace("\u200b", "")
                        .replace(u'\xa0', u' ')
                        .replace("", "")
                )
                content_list.append(content_merge_list)
        return content_list

    def save_content_list(self, content_list):
        # 保存数据到本地
        with open(self.filename, 'a', encoding='utf-8') as f:
            for contents in content_list:
                for content in contents:
                    if len(content) < 5:
                        continue
                    f.write(content + '\n')

    def exetute_requests_item_save(self):
        # 单个请求任务完整执行逻辑
        url = self.queue.get()  # 从队列中拿出一个URL
        print(url)
        html_str = self.parse_url(url)  # 发起请求获取响应内容
        content_list = self.get_content_list(html_str)  # 解析响应内容，返回初步清洗文本
        self.save_content_list(content_list)  # 保存到本地文件
        self.total_response_num += 1  # 任务完成数量加1，单线程所有任务完成

    def _callback(self, temp):
        # 保证函数能够被异步重复执行，self.is_running作用为递归退出条件
        if self.is_running:
            self.pool.apply_async(self.exetute_requests_item_save, callback=self._callback)

    def run(self):
        # 主程序
        self.get_url_list()  # 执行该方法，将所有详情页的url加入到队列

        for i in range(5):  # 控制并发
            self.pool.apply_async(self.exetute_requests_item_save, callback=self._callback)

        while True:  # 防止主线程结束
            # time.sleep(0.0001)  # 避免cpu空转，浪费资源
            print("总任务数%s个,已完成任务%s个" % (self.total_requests_num, self.total_response_num))
            if self.total_response_num >= self.total_requests_num:
                self.is_running = False
                break

        self.pool.close()  # 关闭线程池，防止新的线程开启
        # self.pool.join()  # 等待所有的子线程结束


if __name__ == '__main__':
    news = NewsSpider()
    news.run()
