import configparser
import json
import logging
import sys

# 密钥
send_key = {}
# up列表
up_list = []
# headers
headers_bili = {
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
    "Cookie": "",
    "Host": "api.bilibili.com",
    "Origin": "https://space.bilibili.com",
    "Referer": "https://space.bilibili.com/525121722/dynamic",
    "sec-ch-ua": '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57",
}


# 读取配置文件
def readConfig():
    global send_key, up_list, headers_bili  # 声明为全局变量
    config = configparser.ConfigParser()
    config.read("./config.ini")
    logging.info("读取配置文件", config)
    if "data" in config:
        send_key["token"] = config["data"]["send_key"]
        headers_bili["Cookie"] = config["data"]["cookie_bili"]
        up_list = json.loads(config["data"]["up_list"])  # 使用 json.loads 解析
    else:
        logging.error("配置文件未找到或格式错误")
        sys.exit(0)


# 在模块加载时读取配置
readConfig()
