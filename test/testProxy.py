import requests
import parsel

def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()

def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

# 提取数据
def get_data(data):
    selector = parsel.Selector(data)
    xpath_expression = "//div[@class='property']"
    divs = selector.xpath(xpath_expression)

    # 如果当前页面没有数据，返回 False
    if not divs:
        return False

    for div in divs:
        # 房名
        title = div.xpath(".//div[@class='property-content']//h3/text()").get(default="无标题")
        # 房价
        price = div.xpath(".//div[@class='property-price']//span/text()").get(default="无价格")
        # 位置：提取所有 <span> 中的文本
        positions = div.xpath(".//p[@class='property-content-info-comm-address']/span/text()").getall()
        position = '-'.join(positions) if positions else '未知位置'

        # 打印房源信息
        print(f"房源信息: {title}\t{position}\t{price}")


def getHtml(url, headers):
    retry_count = 30
    while retry_count > 0:
        proxy = get_proxy().get("proxy")
        proxies = {
            "http": "http://" + proxy,
            "https": "http://" + proxy
            }
        print(get_proxy().get("proxy"))
        try:
            # 使用代理访问
            html = requests.get(url=url, headers=headers, proxies=proxies, timeout=5)
            f = open('./data/p_3.html', 'w', encoding='utf-8')
            f.write(html.text)
            f.close()
            print("爬取成功")
            get_data(html.text)
            return True
        except Exception:
            retry_count -= 1
            # 删除代理池中代理
            delete_proxy(proxy)
    return None

url = "https://wuhan.anjuke.com/sale/p1/?from=esf_list"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Cookie":  "aQQ_ajkguid=3CA5E24D-247C-44FD-9E3F-6D28E21E569D; sessid=5A00BB77-8287-42CA-9800-F5952974A9F5; ajk-appVersion=; id58=Cr4A2Wbta7Q52sUIHAP+Ag==; xxzlclientid=eee16be4-5229-4972-a6ff-1726835637144; xxzlxxid=pfmxYBIGZjqG7smlG9onwVYXB6SLni8I9YjtZKpTCcvCO/z69FfwRyLwwMFlpIlfP10x; ctid=22; fzq_h=26d3b7c046e744f75ba5ae2f716cc081_1729042014853_998bb6cd38b2472cb94f440446765720_1746730543; fzq_js_anjuke_ershoufang_pc=e279987116902c61872e31e0dec7697d_1729080567676_24; twe=2; obtain_by=2; xxzlbbid=pfmbM3wxMDM0NnwxLjEwLjB8MTcyOTA4MDU3MTYzMTA1NDU3OHx0K2lIOXBGU3lHM2Z6ajN6enJHYXVibWt6SWxXSDVieEtkNmtaZkNjckxJPXwyOTY5MDQ2NjJmNzdjOGVlNGEwNDc3NGYzYTJlZmVjOV8xNzI5MDgwNTcwMjgyXzkzN2Y0ZGNiMGNlNzQ0ODRiNjY3M2Q1N2FlNGYxZWM0XzE3NDY3MTU5MTh8YWU2MTg0OTkyYWMyZmY4MGI3Mzg4MGUwMjdlN2NiMTBfMTcyOTA4MDU3MDYzN18yNTY="
}

getHtml(url, headers)
# f = open('data/p_test.html', 'r')
# get_data(f.read())

