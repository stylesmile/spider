# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/11/4 22:43
# @File    : 挪威语vildmedkrimi网络评论.py
# @Date    : 2019/11/4
# @Author  : Yuwenjun
# @Desc    : https://www.hamropatro.com/posts


import requests
from lxml import etree
from queue import Queue
from multiprocessing.dummy import Pool
import re
from retrying import retry
import time

letter_regex = re.compile(r'[a-zA-z]')
special_symbol = re.compile(r"[#',\\/<=>，。★、【】《》？“”‘’！[\]_`{|\u4e00-\u9fa5}~]+")


class NewsSpider:
    def __init__(self):
        self.url_temp = "https://vildmedkrimi.dk/page/{}/"
        self.url_temp_header = "https://www.hamropatro.com/posts/"
        self.host_header = "https://www.hamropatro.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, "
                          "like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
            'Referer': 'https://www.hamropatro.com/',
            # 'Connection': 'close'
        }
        self.queue = Queue()
        self.pool = Pool(5)
        self.cookies = {"security_session_mid_verify": "e63dce6af1e6dee46a3a145b79f7557d"}
        self.is_running = True
        self.total_requests_num = 0
        self.total_response_num = 0

    def parse_url_list(self, html):
        html = etree.HTML(html)
        url_list = html.xpath("//a[@class='moretag']/@href")
        return url_list

    def parse_url_detail_list(self, html):
        html = etree.HTML(html)
        url_list = html.xpath("//div[@class='column8']/div/div/div/div[@class='blogTitle']/a/@href")
        return url_list

    def get_url_list(self):  # 获取url列表
        try:
            for i in range(1, 75):
                html = self.parse_url(self.url_temp)
                url_list = self.parse_url_list(html)
                for url in url_list:
                    self.queue.put(self.host_header + url)
                    self.total_requests_num += 1
        except Exception as e:
            print(e)

    @retry(stop_max_attempt_number=3)
    def parse_url(self, url):  # 发送请求，获取响应
        time.sleep(0.5)
        response = requests.get(url, headers=self.headers, timeout=0.5)
        # session = requests.session()
        # response = session.get(url, headers=self.headers, timeout=2, proxies=proxies)
        return response.content.decode()

    def split_content(self, content):
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
                if v == "|":
                    content_list.append(content[e:k + 1].strip())
                    e = k + 1
                if v == "!":
                    content_list.append(content[e:k + 1].strip())
                    e = k + 1
            else:
                content_list.append(content[e:].strip())
        return content_list

    def get_content_list(self, html_str):  # 提取段子
        html = etree.HTML(html_str)
        contents = html.xpath("//p/text()")
        content_list = []
        print(contents)
        for content in contents:
            # if letter_regex.findall(content):
            #     continue
            if content.strip():
                content_merge_list = self.split_content(content.replace(u'\xa0', u' ').replace("<br>", ""))
                content_list.append(content_merge_list)
        return content_list

    def save_content_list(self, content_list):  # 保存数据
        with open('挪威语vildmedkrimi网络评论.txt', 'a', encoding='utf-8') as f:
            for contents in content_list:
                for content in contents:
                    if len(content) < 5:
                        continue
                    f.write(content + '\n')

    def exetute_requests_item_save(self):
        url = self.queue.get()
        print(url)
        html_str = self.parse_url(url)
        content_list = self.get_content_list(html_str)
        self.save_content_list(content_list)
        self.total_response_num += 1

    def _callback(self, temp):
        if self.is_running:
            self.pool.apply_async(self.exetute_requests_item_save, callback=self._callback)

    def run(self):
        self.get_url_list()

        for i in range(2):  # 控制并发
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
