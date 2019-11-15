# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/10/21 10:15
# @File    : 中国国际广播电台新闻爬虫.py
# @Date    : 2019/10/21
# @Author  : Yuwenjun
# @Desc    : https://www.nrk.no/sport/

# request库官方文档
# https://requests.kennethreitz.org//zh_CN/latest/user/quickstart.html

import requests  # request库，根据URL发起请求获取响应
from lxml import etree  # xpath 解析HTML
from queue import Queue  # 队列，保证每个子线程任务唯一
from multiprocessing.dummy import Pool  # 线程池
import time  # 时间模块
import re


letter_regex = re.compile(r'[a-zA-Z]')


class NewsSpider:
    def __init__(self):
        self.url_temp = "https://www.nrk.no/serum/api/render/{}?size=12&perspective=BRIEF&alignment=CENTER" \
                        "&scope=FRONTPAGE&arrangement.offset={}&arrangement.startoffset=1&arrangement.quantity=12" \
                        "&arrangement.repetition=PATTERN&arrangement.view%5B0%5D.perspective=LEAN&arrangement.view" \
                        "%5B0%5D.size=6&arrangement.view%5B0%5D.alignment=RIGHT&arrangement.view%5B1%5D.perspective" \
                        "=LEAN&arrangement.view%5B1%5D.size=6&arrangement.view%5B1%5D.alignment=RIGHT&arrangement" \
                        ".view%5B2%5D.perspective=LEAN&arrangement.view%5B2%5D.size=6&arrangement.view%5B2%5D" \
                        ".alignment=RIGHT&arrangement.view%5B3%5D.perspective=LEAN&arrangement.view%5B3%5D.size=6" \
                        "&arrangement.view%5B3%5D.alignment=RIGHT&arrangement.view%5B4%5D.perspective=LEAN" \
                        "&arrangement.view%5B4%5D.size=6&arrangement.view%5B4%5D.alignment=RIGHT&paged=SIMPLE"  #
        # 用于拼接的URL地址，加大括号是为了format赋值
        self.url_temp_header = "https://www.nrk.no/sport/"  # 首页URL地址
        self.host_header = "https://www.nrk.no/serum/api/render/"  # 相当于host，用于拼接全详情也URL
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/604.1.34 (KHTML, "
                                      "like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
                        "referer": "https://www.nrk.no/sport/"
                        }
        self.queue = Queue()  # 实例化一个队列
        self.pool = Pool(5)  # 实例化一个线程池，最大为5
        self.cookies = {"security_session_mid_verify": "e63dce6af1e6dee46a3a145b79f7557d"}  # 针对一些有反爬措施的网站，带上cookie
        self.is_running = True  # 回调标志位
        self.total_requests_num = 0  # 待完成任务数量
        self.total_response_num = 0  # 完成任务数量

    def parse_url_list(self, html):
        # 解析列表页HTML，获取详情页URL列表
        html = etree.HTML(html)
        url_list = html.xpath("//a[@class='autonomous']/@href")
        return url_list

    def get_url_list(self):
        # 构造URL列表页网址，拼接补全详情页URL，并加入到队列
        next_url = None
        try:
            for i in range(0, 1000):  # range为左闭右开，表示从1到100循环，i代表每次循环的值
                if i == 0:  # 针对首页不带后缀的，使用头URL
                    html = self.parse_url(self.url_temp_header)
                    next_url = self.get_head_click_url(html)[0]
                else:
                    # print(data_id)
                    html = self.parse_url(self.host_header + next_url)
                    next_url = self.get_click_url(html)[0]
                    # data_id = self.get_url_data_id(html)
                # 获取详情页URL，并将详情页URL加入到任务队列
                url_list = self.parse_url_list(html)
                print(url_list)
                for url in url_list:
                    self.queue.put(self.host_header + url)  # 队列任务加1
                    self.total_requests_num += 1  # 数量加1
        except Exception as e:
            print(e)

    def get_button_data_id(self, html):
        html = etree.HTML(html)
        data_id = html.xpath("//button[@class='flow-page-forward nrk-button nrk-color-base']/@data-id")
        index = data_id[0].find("?")
        return data_id[0][:index]

    def get_click_url(self, html):
        html = etree.HTML(html)
        url = html.xpath("//input[@class='next-data-id']/@value")
        return url

    def get_head_click_url(self, html):
        html = etree.HTML(html)
        url = html.xpath("//button[@class='flow-page-forward nrk-button nrk-color-base']/@data-id")
        return url

    def parse_url(self, url):
        # 发送请求，获取响应
        response = requests.get(url, headers=self.headers, timeout=5)
        # 需要session的话，注释掉上面的代码，使用下面代码
        # session = requests.session()
        # response = session.get(url, headers=headers)
        return response.content.decode()  # conten方法解析不出内容的话，换成text

    def split_content(self, content):
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
                        content_list.append(content[e:k + 1].strip())
                        e = k + 1
                if v == "?":
                    if content[k - 1] != "?" and content[k + 1] != "?" and content[k + 1] != ")":
                        content_list.append(content[e:k + 1].strip())
                        e = k + 1
                # if v == ";" and len(content) > 200:
                #     content_list.append(content[e:k + 1].strip())
                #     e = k + 1
                if v == "!":
                    content_list.append(content[e:k + 1].strip())
                    e = k + 1
            else:
                content_list.append(content[e:].strip())
        return content_list

    def get_content_list(self, html_str):
        # 提取详情也的文本内容，返回文本列表
        html = etree.HTML(html_str)
        contents = html.xpath("//div[@itemprop='articleBody']/p/text()")
        content_list = []
        print(contents)
        for content in contents:
            # if letter_regex.findall(content):
            #     continue
            if content.strip():
                content_merge_list = self.split_content(content.replace("\u200b", "").replace(u'\xa0', u' '))
                content_list.append(content_merge_list)
        return content_list

    def save_content_list(self, content_list):
        # 保存数据到本地
        with open('挪威语nrk体育新闻.txt', 'a', encoding='utf-8') as f:
            for contents in content_list:
                for content in contents:
                    if len(content) < 5:
                        continue
                    f.write(content + '\n')

    def exetute_requests_item_save(self):
        try:
            # 单个请求任务完整执行逻辑
            url = self.queue.get()  # 从队列中拿出一个URL
            print(url)
            html_str = self.parse_url(url)  # 发起请求获取响应内容
            content_list = self.get_content_list(html_str)  # 解析响应内容，返回初步清洗文本
            self.save_content_list(content_list)  # 保存到本地文件
            self.total_response_num += 1  # 任务完成数量加1，单线程所有任务完成
        except Exception as e:
            print(e)
            self.queue.put(url)

    def _callback(self, temp):
        # 保证函数能够被异步重复执行，self.is_running作用为递归退出条件
        if self.is_running:
            self.pool.apply_async(self.exetute_requests_item_save, callback=self._callback)

    def run(self):
        # 主程序
        self.get_url_list()  # 执行该方法，将所有详情页的url加入到队列

        for i in range(10):  # 控制并发
            self.pool.apply_async(self.exetute_requests_item_save, callback=self._callback)

        while True:  # 防止主线程结束
            time.sleep(0.0001)  # 避免cpu空转，浪费资源
            # print("总任务数%s个,已完成任务%s个" % (self.total_requests_num, self.total_response_num))
            if self.total_response_num >= self.total_requests_num:
                self.is_running = False
                break

        self.pool.close()  # 关闭线程池，防止新的线程开启
        # self.pool.join()  # 等待所有的子线程结束


if __name__ == '__main__':
    news = NewsSpider()
    news.run()
