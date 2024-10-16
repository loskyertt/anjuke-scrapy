import re
import requests

# 代理地址，设置为你本地代理的地址和端口
proxy = {
    'http': 'http://localhost:7890',
    'https': 'http://localhost:7890',
}

# 访问外部API，获取代理IP
try:
    response = requests.get('http://api.ipify.org', proxies=proxy)
    current_ip = response.text
    print(f"Current proxy IP: {current_ip}")
except requests.RequestException as e:
    print(f"Error retrieving IP: {e}")

# 正则表达式提取代理IP和端口
proxy_address = proxy['http']
match = re.match(r'http://([^\:]+):(\d+)', proxy_address)

if match:
    ip = match.group(1)  # 提取IP地址
    port = match.group(2)  # 提取端口号
    print(f"IP: {ip}, Port: {port}")
else:
    print("Invalid proxy format")
