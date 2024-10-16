from DrissionPage import Chromium, ChromiumOptions
import parsel
import time
import random
import pandas as pd
from datetime import datetime


# 解析数据
def getData(data):
    selector = parsel.Selector(data)
    xpath_expression = '//li[@class="item-wrap"]'
    divs = selector.xpath(xpath_expression)
    results = []
    for div in divs:
        title = div.xpath('.//span[@class="content-title"]/text()').get()
        price = div.xpath('.//span[@class="content-price"]/text()').get()
        results.append((title, price))
    return results


# 保存数据
def save_to_csv(data, filename):
    df = pd.DataFrame(data, columns=['房名', '价格'])
    df.to_csv(filename, mode='a', header=not pd.io.common.file_exists(
        filename), index=False, encoding='utf-8-sig')


# 滑动页面
def scroll_and_scrape(tab, max_attempts=5):
    last_data = set()
    unchanged_count = 0
    total_count = 0
    csv_filename = f"anjuke_data_{
        datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    while unchanged_count < max_attempts:
        # 滚动到页面底部
        tab.scroll.to_bottom()
        time.sleep(random.uniform(2.5, 4))

        html_data = tab.html
        current_data = getData(html_data)
        current_set = set(current_data)

        new_data = current_set - last_data

        print(f"\n--- 滚动后的数据状态 ---")
        print(f"当前总数据量: {len(current_data)}")
        print(f"新增数据量: {len(new_data)}")

        if new_data:
            print("新加载的数据:")
            for title, price in new_data:
                print(f"房名：{title}\t，房价：{price}万")
            print("-------------------------")

            # 追加新数据
            save_to_csv(new_data, csv_filename)

            last_data = current_set
            unchanged_count = 0
            total_count += len(new_data)
        else:
            print("本次滚动未检测到新数据")
            unchanged_count += 1

        print(f"累计获取数据量: {total_count}")

    return total_count, csv_filename


if __name__ == "__main__":
    co = ChromiumOptions()
    co.no_imgs(True)        # 不加载图片
    # 用本机代理（可以手动切换节点来实现切换IP），需要把配置文件里的大 anjuke.com 添加到代理组
    co.set_proxy('http://localhost:7890')
    co.set_user_agent(
        user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')

    url = "https://m.anjuke.com/wh/sale/?from=TW_HOME"
    browser = Chromium(addr_or_opts=co)
    tab = browser.latest_tab
    tab.get(url=url)

    total_data_count, csv_file = scroll_and_scrape(tab)

    print(f"\n爬取结束，总共获取到 {total_data_count} 条数据")
    print(f"数据已保存到: {csv_file}")

    browser.quit()
