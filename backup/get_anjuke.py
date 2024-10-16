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
        logging.warning("No property divs found. The page structure might have changed.")
        return False

    data_found = False
    for div in divs:
        title = div.xpath(".//div[@class='property-content']//h3/text()").get()
        position = div.xpath(".//div[@class='property-content-info property-content-info-comm']//span/text()").get()
        price = div.xpath(".//div[@class='property-price']//span/text()").get()

        if title and position and price:
            logging.info(f"Extracted: {title}\t{position}\t{price}")
            save_to_csv(filename, title, position, price)
            data_found = True
        else:
            logging.warning(f"Incomplete data: title={title}, position={position}, price={price}")

    logging.info(f"Exiting get_data function. Data found: {data_found}")
    return data_found

def fetch_page(url, headers, proxies, max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to fetch {url}")
            response = requests.get(url=url, headers=headers, proxies=proxies, timeout=30)
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
    filename = "./data/anjuke_data_01.csv"

    page = 1
    consecutive_name_resolution_errors = 0
    max_consecutive_name_resolution_errors = 5

    while True:
        url = base_url.format(page)
        logging.info(f"Processing page {page}: {url}")

        html_data, error = fetch_page(url, headers, proxies)

        if html_data is None:
            if "NameResolutionError" in error:
                consecutive_name_resolution_errors += 1
                logging.warning(f"Consecutive name resolution error count: {consecutive_name_resolution_errors}")
                if consecutive_name_resolution_errors >= max_consecutive_name_resolution_errors:
                    logging.error(f"Reached maximum allowed consecutive name resolution errors ({max_consecutive_name_resolution_errors}). Stopping.")
                    break
            else:
                logging.error(f"Failed to fetch page {page} due to non-name resolution error. Continuing to next page.")
                page += 1
                continue
        else:
            consecutive_name_resolution_errors = 0
            logging.info(f"Successfully fetched page {page}. Attempting to extract data.")

            if not get_data(data=html_data, filename=filename):
                logging.info(f"No data found on page {page}. Stopping.")
                break

        wait_time = random.uniform(5, 10)
        logging.info(f"Waiting for {wait_time:.2f} seconds before next request.")
        sleep(wait_time)
        page += 1

    logging.info("Scraping finished.")