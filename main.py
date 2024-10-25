import sys
import time
import random
import logging
from script.push import push, push_dynamic
from bili.index import bili_main
from config import send_key, headers_bili, up_list

# 写入日志
logging.basicConfig(
    filename="running.log",
    format="\n%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

def Wlog(text):
    logging.error(text, exc_info=True)


def test():
    if ii == 2:
        text = "测试...,test..."
        push("测试", text)
        # push_dynamic("测试", 1, text)
        logging.info(text)


ii = 0


def main():
    # 在这里使用 send_key、headers_bili 和 up_list
    logging.info(f"Send Key: {send_key}")
    logging.info(f"Headers: {headers_bili}")
    logging.info(f"UP List: {up_list}")
    bili_main()
    # global ii
    # while True:
    #     ii = ii + 1
    #     logging.info("当前轮次: " + str(ii))
    #     # test()
    #     bili_main()
    #     s = random.randint(30, 80)
    #     time.sleep(s * 2)


if __name__ == "__main__":
    logging.info("------ 开始监控 ------")
    try:
        # readConfig()
        main()
    except Exception as e:
        Wlog("")
        print("程序异常退出", e)
        # push('异常','程序异常退出,请登录远程查看日志')
