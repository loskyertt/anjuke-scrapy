import requests
import parsel
import csv
from time import sleep, time  # 导入 time 来记录时间
import random
from requests.exceptions import RequestException, ProxyError
from urllib3.exceptions import NameResolutionError, MaxRetryError
import logging
import threading

# 锁对象，用于保护 CSV 文件写入
lock = threading.Lock()


# 获取当前代理 IP
def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


# 删除当前代理 IP
def delete_proxy(proxy):
    requests.get(f"http://127.0.0.1:5010/delete/?proxy={proxy}")


# 保存到 csv 文件 (加锁确保线程安全)
def save_to_csv(filename: str, title, position, price):
    with lock:
        with open(filename, mode='a', encoding='utf-8', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow([title, position, price])


# 提取数据
def get_data(data, filename=None):
    selector = parsel.Selector(data)
    xpath_expression = "//div[@class='property']"
    divs = selector.xpath(xpath_expression)

    # 如果当前页面没有数据，返回 False
    if not divs:
        return False

    for div in divs:
        title = div.xpath(".//div[@class='property-content']//h3/text()").get()
        position = div.xpath(
            ".//div[@class='property-content-info property-content-info-comm']//span/text()").get()
        price = div.xpath(".//div[@class='property-price']//span/text()").get()

        if title and position and price:
            print(f"房源信息: {title}\t{position}\t{price}")
            save_to_csv(filename, title, position, price)

    return True  # 如果有数据，返回 True


# 获取页面信息
def fetch_page(url, headers, filename, max_retries=15, delay=5):
    for attempt in range(max_retries):
        # 每次尝试时获取一个新的代理
        proxy = get_proxy().get("proxy")
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
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
                sleep(delay)  # 随机延迟
                continue  # 重试

            print(f"页面获取成功: {url}")
            return get_data(response.text, filename)

        except (RequestException, NameResolutionError, MaxRetryError, ProxyError) as e:
            logging.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")
            delete_proxy(proxy)  # 删除代理后重新获取
            if attempt < max_retries - 1:
                logging.info(f"{delay} 秒后重试...")
                sleep(delay)
            else:
                logging.error(f"重试次数已达上限，无法获取页面: {url}")
                return False


# 手动创建并管理线程
if __name__ == "__main__":
    # 记录日志信息
    logging.basicConfig(
        filename='scraper_ts.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    headers = {
        "User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Cookie":  "aQQ_ajkguid=3CA5E24D-247C-44FD-9E3F-6D28E21E569D; sessid=5A00BB77-8287-42CA-9800-F5952974A9F5; ajk-appVersion=; id58=Cr4A2Wbta7Q52sUIHAP+Ag==; xxzlclientid=eee16be4-5229-4972-a6ff-1726835637144; xxzlxxid=pfmxYBIGZjqG7smlG9onwVYXB6SLni8I9YjtZKpTCcvCO/z69FfwRyLwwMFlpIlfP10x; ctid=22; fzq_h=26d3b7c046e744f75ba5ae2f716cc081_1729042014853_998bb6cd38b2472cb94f440446765720_1746730543; fzq_js_anjuke_ershoufang_pc=e279987116902c61872e31e0dec7697d_1729080567676_24; twe=2; obtain_by=2; xxzlbbid=pfmbM3wxMDM0NnwxLjEwLjB8MTcyOTA4MDU3MTYzMTA1NDU3OHx0K2lIOXBGU3lHM2Z6ajN6enJHYXVibWt6SWxXSDVieEtkNmtaZkNjckxJPXwyOTY5MDQ2NjJmNzdjOGVlNGEwNDc3NGYzYTJlZmVjOV8xNzI5MDgwNTcwMjgyXzkzN2Y0ZGNiMGNlNzQ0ODRiNjY3M2Q1N2FlNGYxZWM0XzE3NDY3MTU5MTh8YWU2MTg0OTkyYWMyZmY4MGI3Mzg4MGUwMjdlN2NiMTBfMTcyOTA4MDU3MDYzN18yNTY="
    }

    base_url = "https://wuhan.anjuke.com/sale/p{}/?from=esf_list"
    filename = "anjuke_data_ts.csv"
    max_pages = 5  # 设置最大爬取页面数

    # 开始时间
    start_time = time()

    threads = []
    for page in range(1, max_pages + 1):
        url = base_url.format(page)
        thread = threading.Thread(
            target=fetch_page, args=(url, headers, filename))
        thread.start()  # 启动线程
        threads.append(thread)  # 将线程保存到线程列表中

        # 随机延时，避免反爬
        sleep_time = random.uniform(1, 3)
        sleep(sleep_time)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 结束时间
    end_time = time()

    total_time = end_time - start_time
    print(f"完成爬取！总耗时: {total_time:.2f} 秒")
