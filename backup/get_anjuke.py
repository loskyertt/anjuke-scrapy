import requests
import re
import parsel
import csv
from time import sleep
import random
import logging
from requests.exceptions import RequestException
from urllib3.exceptions import NameResolutionError, MaxRetryError

logging.basicConfig(filename='./logs/scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# 获取主机代理 IP
def get_proxy() -> list[str]:

    # 代理地址，设置为本地代理的地址和端口
    proxy = {
        # 记得改成自己的端口号
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
        # ip = match.group(1)  # 提取IP地址
        port = match.group(2)  # 提取端口号
        # print(f"IP: {ip}, Port: {port}")
        return current_ip, port
    else:
        print("Invalid proxy format")


def save_to_csv(filename: str, title, position, price):
    with open(filename, mode='a', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([title, position, price])
    logging.info(f"Data saved: {title}, {position}, {price}")


def get_data(data, filename) -> bool:
    logging.info("Entering get_data function")
    selector = parsel.Selector(data)
    xpath_expression = "//div[@class='property']"
    divs = selector.xpath(xpath_expression)

    if not divs:
        logging.warning(
            "No property divs found. The page structure might have changed.")
        print("无法解析页面信息！")
        return False

    data_found = False
    for div in divs:
        title = div.xpath(".//div[@class='property-content']//h3/text()").get()
        positions = div.xpath(
            ".//p[@class='property-content-info-comm-address']/span/text()").getall()
        position = '-'.join(positions) if positions else '未知位置'
        price = div.xpath(".//div[@class='property-price']//span/text()").get()

        print(f"{title}, {position}, {price}")
        logging.info(f"Extracted: {title}\t{position}\t{price}")
        save_to_csv(filename, title, position, price)
        data_found = True

    logging.info(f"Exiting get_data function. Data found: {data_found}")
    return data_found


def fetch_page(url, headers, proxies, max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to fetch {url}")
            response = requests.get(
                url=url, headers=headers, proxies=proxies, timeout=30)
            response.raise_for_status()
            logging.info(f"Successfully fetched {url}")
            return response.text, None
        except (RequestException, NameResolutionError, MaxRetryError) as e:
            error_message = str(e)
            logging.warning(f"Attempt {attempt + 1} failed: {error_message}")
            if attempt < max_retries - 1:
                sleep_time = delay * (attempt + 1)
                logging.info(f"Retrying in {sleep_time} seconds...")
                sleep(sleep_time)
            else:
                logging.error(f"Max retries reached. Unable to fetch {url}")
                return None, error_message


if __name__ == "__main__":
    ip, port = get_proxy()  # 确保这个函数正确实现
    proxies = {
        "http://": f"http://{ip}:{port}",
        "https://": f"http://{ip}:{port}"
    }
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "cookie":  "aQQ_ajkguid=3CA5E24D-247C-44FD-9E3F-6D28E21E569D; sessid=5A00BB77-8287-42CA-9800-F5952974A9F5; ajk-appVersion=; id58=Cr4A2Wbta7Q52sUIHAP+Ag==; xxzlclientid=eee16be4-5229-4972-a6ff-1726835637144; xxzlxxid=pfmxYBIGZjqG7smlG9onwVYXB6SLni8I9YjtZKpTCcvCO/z69FfwRyLwwMFlpIlfP10x; ctid=22; fzq_h=7d1305571441ded6fe89e8170a5413e6_1728638021185_7618a62a84244908b01ae2ef54833a19_2554535716; fzq_js_anjuke_ershoufang_pc=182f073b1e1a055ae746ac5e5efc673e_1728638022689_25; twe=2; obtain_by=2; xxzlbbid=pfmbM3wxMDM0NnwxLjEwLjB8MTcyODYzODAyNTYzMzg0NTUxMnwyV1NlTmRseXg3djdFNzlhVkZkN3hmZGZyNVcxYjh3VFdNT1c4enVFelg0PXxiZTlhYzU5Nzg4ODQ5ZjQwMzEwNjg5NGI2NWUzMTk3M18xNzI4NjM4MDI0MTg5XzZiZDVmYzFkMmJkZjQ0YTZiYjRjMzk0NjkyYmU3YTQzXzI1NTQ1MzU3MTZ8MzU2MjMxMWJiYzAyZWJiNTk0Njg3ZjRlNmJlMDQ0NjdfMTcyODYzODAyNDY3OF8yNTU="
    }

    base_url = "https://wuhan.anjuke.com/sale/p{}/?from=esf_list"
    filename = "./data/anjuke_data_03.csv"

    page = 1
    consecutive_name_resolution_errors = 0  # 用于记录解析错误次数
    max_consecutive_name_resolution_errors = 5  # 最大解析次数

    consecutive_empty_pages = 0  # 记录连续空页次数
    max_empty_pages = 10  # 设置最大连续空页数

    while True:

        url = base_url.format(page)
        print(f"正在爬取第 {page} 页: {url}")

        # 获取 HTML
        html_data, error = fetch_page(url, headers, proxies)

        if html_data is None:
            if "NameResolutionError" in error:
                consecutive_name_resolution_errors += 1
                logging.warning(
                    f"连续第 {consecutive_name_resolution_errors} 次遇到名称解析错误！")
                if consecutive_name_resolution_errors >= max_consecutive_name_resolution_errors:
                    logging.error(f"达到最大连续名称解析错误次数，爬取终止！")
                    break
            else:
                logging.error(f"无法获取第 {page} 页，错误信息: {error}，继续尝试下一页")
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
        sleep_time = random.uniform(2, 5)
        print(f"等待 {sleep_time:.2f} 秒后继续...")
        sleep(sleep_time)
        page += 1
