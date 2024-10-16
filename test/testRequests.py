# -*- coding: utf-8 -*-
'''
@File    :   test.py
@Time    :   2024/09/19 14:38:28
@Author  :   loskyertt
@Blog    :   https://loskyertt.github.io/
@Desc    :   None
'''

import requests     # 发送请求用的
from bs4 import BeautifulSoup
import re
import parsel


# 获取当前代理 ip 和 port
def get_IP():
    proxy = {
        'http': 'http://localhost:7890',
        'https': 'http://localhost:7890',
    }

    # 访问外部API，获取代理IP
    try:
        response = requests.get('http://api.ipify.org', proxies=proxy)
        current_ip = response.text
        # print(f"Current proxy IP: {current_ip}")
    except requests.RequestException as e:
        print(f"Error retrieving IP: {e}")

    # 正则表达式提取代理IP和端口
    proxy_address = proxy['http']
    match = re.match(r'http://([^\:]+):(\d+)', proxy_address)

    if match:
        ip = match.group(1)  # 提取IP地址
        port = match.group(2)  # 提取端口号
        # print(f"IP: {ip}, Port: {port}")
        return current_ip, port
    else:
        print("Invalid proxy format")


# 发送请求，获取数据
def askURL(url, proxies):
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "cookie": "aQQ_ajkguid=76DEB12B-A793-419C-A1C8-65F51FEE195E; sessid=187D23AE-EDB0-49D7-B620-D744BAFF8229; ajk-appVersion=; fzq_h=389d9139fcdfd8653b9878b9f819cbcc_1726730178180_005a6d68bb3a48469bc39487a201974e_1899572285; id58=CrIHZ2brz8NDbl3EyyZDAg==; xxzlclientid=4b19919d-67b1-48ee-a82e-1726730179624; xxzlxxid=pfmxYBIGZjqG7smlG9onwVYXB6SLni8I9YjtZKpTCcvCO/wVkufcSFde0Q/jQnBo30Oa; obtain_by=2; twe=2; ctid=22; fzq_js_anjuke_ershoufang_m=775656719901e7570827e5736ae53afe_1726734575531_29; xxzlbbid=pfmbM3wxMDM0NnwxLjEwLjF8MTcyNjczNDU3NjM3MzY0NTg4OXxQanZ1SnQ2R2syWkhjU29xTTRSdTg0QkQ1dDN0eXNwZ09Xd2pEb09LTHBVPXw3Y2Y2MmQzN2M4YTEzNWNkZjg1MjM2MGZiNmNlNGI2Zl8xNzI2NzM0NTc1ODQwXzBlNGJjYTFlMzI4MTQzNDY4N2JjYWM5OTMyOWYwZGY3XzE1MDQxOTM1Mzh8ZDc0N2U2ZmYwN2Q2ZDI0MzBkOTgxM2IwNTM0MjdmZjlfMTcyNjczNDU3NjEwM18yNTc="
    }
    response = requests.get(url=url, headers=headers, proxies=proxies)
    html_data = response.text
    # print(html_data)
    return html_data


# 提取数据
def getDate(data):
    selector = parsel.Selector(data)
    xpath_expression = '//li[@class="item-wrap"]'
    divs = selector.xpath(xpath_expression)
    for div in divs:
        title = div.xpath('.//span[@class="content-title"]/text()').get()
        price = div.xpath('.//span[@class="content-price"]/text()').get()

        print(title)


if __name__ == "__main__":

    ip, port = get_IP()
    # print(ip, type(ip))
    # print(port, type(port))
    proxies = {
        'http://': 'http://' + ip + ':' + port,
        'https://': 'http://' + ip + ':' + port
    }
    url = "https://m.anjuke.com/wh/sale/?from=TW_HOME"

    data = askURL(url=url, proxies=proxies)
    getDate(data=data)
