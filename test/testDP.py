from DrissionPage import Chromium, ChromiumOptions

# 创建配置对象（默认从 ini 文件中读取配置）
co = ChromiumOptions()
# 设置不加载图片、静音
co.no_imgs(True).mute(True)

# 以该配置创建页面对象
page = Chromium(addr_or_opts=co)
tab = page.latest_tab
tab.get("https://m.anjuke.com/wh/sale/?from=TW_HOME")