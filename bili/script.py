from config import headers_bili
import requests
import logging


# 获取全部动态
def getAllDynamic(UP):
    global name

    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={UP["mid"]}"
    res = requests.get(url, headers=headers_bili).json()
    res.raise_for_status()

    # 检查返回数据
    if "data" not in res:
        logging.info(UP["name"] + "动态：返回json不包含data字段")
        return

    dynamic_list = res["data"]["items"]
