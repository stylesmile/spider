# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2019/11/5 16:47
# @File    : hamropatro文学博客.py
# @Date    : 2019/11/5
# @Author  : Yuwenjun
# @Desc    :

import time

from selenium import webdriver
from lxml import etree
import re


letter_regex = re.compile(r'[a-zA-Z]')


class TedSpider:
    def __init__(self):
        self.url_temp = "http://www.hamropatro.com/posts/"
        self.url_temp_header = "https://www.setopati.com/politics"
        self.host_header = "https://www.hamropatro.com/"
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/604.1.34 (KHTML, "
                                      "like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1"}
        self.chrome_driver_path = "E:\software-program\chromedriver_win32\chromedriver.exe"
        self.driver = webdriver.Chrome(executable_path=self.chrome_driver_path)
        self.url_set = set()

    def save_content(self, content_list):
        with open('hamropatro尼泊尔文学博客.txt', 'a', encoding='utf-8') as f:
            for contents in content_list:
                for content in contents:
                    if len(content) < 10:
                        continue
                    f.write(content + '\n')

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
                if v == ";":
                    content_list.append(content[e:k + 1].strip())
                    e = k + 1
                if v == "!":
                    content_list.append(content[e:k + 1].strip())
                    e = k + 1
            else:
                content_list.append(content[e:].strip())
        return content_list

    def get_url_list(self):
        self.driver.get(self.url_temp)
        url_list = self.driver.find_elements_by_xpath("//div[@class='recentArticleListing']/ul/li/a")
        for url in url_list:
            self.url_set.add(url.get_attribute("href"))

    def parse_url(self, url):
        self.driver.get(url)
        ret = self.driver.find_elements_by_xpath("//div[@class='column8']/div/div/div/div[@class='blogTitle']/a")
        detail_url_list = [url.get_attribute('href') for url in ret]
        print(detail_url_list)
        # self.driver.close()
        return detail_url_list

    def get_content_list(self, detail_url_list):
        content_split_list = list()
        for detail_url in detail_url_list:
            detail_url = detail_url
            self.driver.get(detail_url)
            # time.sleep(2)
            contents = self.driver.find_elements_by_xpath("//p")
            for content in contents:
                if not content.text.strip():
                    continue
                # text 文本
                if letter_regex.findall(content.text):
                    continue
                print(content.text)
                content = self.split_content(content.text.strip().replace("&nbsp;", "").replace("&amp;", "&"))
                content_split_list.append(content)
        return content_split_list

    def run(self):
        self.get_url_list()
        for url in self.url_set:
            # 获取url
            detail_url_list = self.parse_url(url)
            print(detail_url_list)
            content_split_list = self.get_content_list(detail_url_list)
            self.save_content(content_split_list)
        self.driver.quit()


if __name__ == '__main__':
    ted = TedSpider()
    ted.run()