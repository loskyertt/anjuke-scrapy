# -*- coding: utf-8 -*-
'''
@File    :   get_anjuke.py
@Time    :   2024/10/10 19:07:01
@Author  :   loskyertt
@Blog    :   https://loskyertt.github.io/
@Desc    :   None
'''

import requests
import parsel
import csv
from time import sleep
import random
from requests.exceptions import RequestException, ProxyError
from urllib3.exceptions import NameResolutionError, MaxRetryError
import logging


# 获取当前代理 IP
def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


# 删除当前代理 IP
def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


# 保存到 csv 文件
def save_to_csv(filename: str, title, position, price):
    with open(filename, mode='a', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([title, position, price])


# 提取数据
def get_data(data, filename):
    selector = parsel.Selector(data)
    xpath_expression = "//div[@class='property']"
    divs = selector.xpath(xpath_expression)

    # 如果当前页面没有数据，返回 False
    if not divs:
        return False

    for div in divs:
        title = div.xpath(
            ".//div[@class='property-content']//h3/text()").get()  # 房名
        position = div.xpath(
            # 位置区域
            ".//div[@class='property-content-info property-content-info-comm']//span/text()").get()
        price = div.xpath(
            ".//div[@class='property-price']//span/text()").get()  # 房价

        if title and position and price:
            print(f"房源信息: {title}\t{position}\t{price}")
            save_to_csv(filename, title, position, price)

    return True  # 如果有数据，返回 True


# 获取页面信息
def fetch_page(url, headers, proxy, max_retries=15, delay=5):
    for attempt in range(max_retries):
        proxies = {
            "http": "http://" + proxy,
            "https": "http://" + proxy
        }
        print(f"第{attempt + 1}次的代理地址和端口：{proxy}")

        try:
            print(f"正在尝试获取页面: {url} (第 {attempt+1} 次尝试)")
            response = requests.get(
                url=url, headers=headers, proxies=proxies, timeout=5)
            response.raise_for_status()

            # 检查是否是反爬虫页面
            if "antibot" in response.text:
                print("检测到反爬虫页面，尝试重新获取页面...")
                delete_proxy(proxy)  # 删除无效代理
                proxy = get_proxy().get("proxy")  # 更新代理
                sleep(delay)  # 延迟
                continue  # 重试

            print(f"页面获取成功: {url}")
            return response.text, None  # 请求成功，返回页面数据

        except (RequestException, NameResolutionError, MaxRetryError, ProxyError) as e:
            logging.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")
            delete_proxy(proxy)  # 只有请求失败时才删除代理
            proxy = get_proxy().get("proxy")  # 更新代理
            if attempt < max_retries - 1:
                logging.info(f"{delay} 秒后重试...")
                sleep(delay)
            else:
                logging.error(f"重试次数已达上限，无法获取页面: {url}")
                return None, str(e)


if __name__ == "__main__":

    # 记录日志信息
    logging.basicConfig(
        filename='./logs/scraper.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "cookie":  "aQQ_ajkguid=65FDD8AE-3D86-4C0E-8CA8-22014CD5B9C4; sessid=02009051-43CC-4F9A-81CB-13B9E84025D8; ajk-appVersion=; id58=CrIIUGbsyhbBhtJSDs5BAg==; xxzlclientid=66a3664f-ccc3-4cf7-9607-1726794267861; xxzlxxid=pfmxNQiSfMKu/8I5kQklBnA9kRqNJprCmqjXuJEVx7msxlKo2USXVwHym11yfdMVD3YJ; ctid=22; fzq_h=343f0622dbbd0a8fbec598b6d424c4b7_1728989542135_a458acc0e91f4db982a3fe6f5d2832aa_1899572437; twe=2; fzq_js_anjuke_ershoufang_pc=a4a7bbf7b77e9650d5571adc6289b87d_1728992775276_23; obtain_by=2; xxzlbbid=pfmbM3wxMDM0NnwxLjEwLjB8MTcyODk5Mjc3OTI0MzU2NTI1MHx0L1U5bXZmSlI2eVpNemNNTnkxbStrMG5yemtCMmdzNzlRdmFrM1lpaTVFPXwwZjgzNzM2M2Y2OGM0ZWYxYzI0OTFmNGY0NGZmZDhkZF8xNzI4OTkyNzc2MjI2X2EzMWI3ZjgyODQwMzRiZjU4M2E3MGNkZjg4NDIyNDQyXzE4OTk1NzI0Mzd8OGFlYTdiOWFiMzU2ZDgyOWQ0MzhmZGMxZjE4ZjU0MTBfMTcyODk5Mjc3NzUwMl8yNTU="
    }

    base_url = "https://wuhan.anjuke.com/sale/p{}/?from=esf_list"
    filename = "./data/anjuke_data_test02.csv"

    page = 1
    consecutive_name_resolution_errors = 0  # 用于记录解析错误次数
    max_consecutive_name_resolution_errors = 5  # 最大解析次数

    consecutive_empty_pages = 0  # 记录连续空页次数
    max_empty_pages = 3  # 设置最大连续空页数

    # 获取初始代理
    proxy = get_proxy().get("proxy")

    while True:

        url = base_url.format(page)
        print(f"正在爬取第 {page} 页: {url}")

        # 获取页面 HTML 数据
        html_data, error = fetch_page(url=url, headers=headers, proxy=proxy)

        if html_data is None:
            # 如果代理无效或者请求失败，才更换代理
            if "NameResolutionError" in error:
                consecutive_name_resolution_errors += 1
                logging.warning(
                    f"连续第 {consecutive_name_resolution_errors} 次遇到名称解析错误！")
                if consecutive_name_resolution_errors >= max_consecutive_name_resolution_errors:
                    logging.error(f"达到最大连续名称解析错误次数，爬取终止！")
                    break
            else:
                logging.error(f"无法获取第 {page} 页，错误信息: {error}，继续尝试下一页")
                proxy = get_proxy().get("proxy")  # 更换代理
                page += 1
                continue
        else:
            consecutive_name_resolution_errors = 0

            if not get_data(data=html_data, filename=filename):
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_empty_pages:
                    logging.info(f"连续 {max_empty_pages} 页没有数据，爬取终止。")
                    break
            else:
                consecutive_empty_pages = 0  # 重置空页计数器
                print(f"第 {page} 页数据成功爬取并保存。")

        # 随机休眠一段时间，模拟人类行为，避免被封禁
        sleep_time = random.uniform(5, 10)
        print(f"等待 {sleep_time:.2f} 秒后继续...")
        sleep(sleep_time)
        page += 1

