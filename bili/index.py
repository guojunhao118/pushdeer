import math
import requests
import time
from datetime import datetime
import copy
import logging
from script.push import push, push_dynamic

push_text_len = 50

up_list = [
    {"name": "莫大", "mid": "525121722", "roomId": "23229268"},
    {"name": "笨笨", "mid": "11473291", "roomId": "27805029"},
]

bili_moda_opus_link = "https://www.bilibili.com/opus/"
m_tg = {}
m_tg_top = {}
m_tg_test = ""
live_start_time = None
noLogin = False

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


# 提取文字
def extract_text_from_dynamic(dynamic):
    """从动态中提取文本内容"""
    if "desc" in dynamic:
        return dynamic["desc"].get("text", "")
    return (
        dynamic.get("archive", {}).get("title", "")
        or dynamic.get("ugc_season", {}).get("title", "")
        or dynamic.get("opus", {}).get("summary", {}).get("text", "")
    )

# 发送请求并处理错误
def fetch_dynamic_data(mid):
    url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={mid}'
    try:
        res = requests.get(url, headers=headers_bili)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"请求错误: {e}")
        return {}

# UP动态（除置顶）
def monitor_bili_up_dynamic(UP):
    global m_tg, noLogin

    # 初始化用户状态
    m_tg.setdefault(UP["mid"], "")
    res = fetch_dynamic_data(UP["mid"])

    # 检查返回数据
    if "data" not in res:
        logging.info(UP["name"] + "动态：返回json不包含data字段")
        return

    items = res["data"]["items"]
    first_item = items[0]

    # 检查是否为置顶动态
    if (
        "module_tag" in first_item["modules"]
        and first_item["modules"]["module_tag"]["text"] == "置顶"
    ):
        # 如果是，动态设置为第二条
        first_item = items[1]

    dynamic_id = first_item["id_str"]
    jump_url = bili_moda_opus_link + dynamic_id
    text = extract_text_from_dynamic(first_item["modules"]["module_dynamic"])

    if text:
        text = text.replace("\n", " ")[:push_text_len]
    else:
        logging.info(UP["name"] + "动态：text类型错误")
        return

    # 检查动态是否已经推送
    if m_tg[UP["mid"]] == "":
        m_tg[UP["mid"]] = dynamic_id
    elif m_tg[UP["mid"]] != dynamic_id:
        push(UP["name"] + "动态", text, jump_url)
        # 推送动态到网站，暂时弃用
        # push_dynamic(
        #     UP["name"],
        #     1,
        #     text,
        #     jump_url,
        #     first_item["modules"]["module_author"]["pub_ts"],
        # )
        m_tg[UP["mid"]] = dynamic_id


# 置顶动态
def monitor_bili_up_top(UP):
    global m_tg_top, noLogin

    m_tg_top.setdefault(UP["mid"], "")

    if noLogin:
        return

    res = fetch_dynamic_data(UP["mid"])

    if "data" not in res or not res["data"].get("items"):
        logging.info(UP["name"] + "置顶：返回json没包含data字段")
        return

    # 查找置顶动态
    top_item = next(
        (
            item
            for item in res["data"]["items"]
            if "module_tag" in item["modules"]
            and item["modules"]["module_tag"]["text"] == "置顶"
        ),
        None,
    )

    if top_item:
        jump_id = top_item["id_str"]
        link = bili_moda_opus_link + jump_id
        fetch_top_reply(jump_id, link, UP)
    else:
        push("异常", "bili cookie失效,请重新登录")
        logging.info("bili cookie失效,请重新登录")
        noLogin = True

# 获取置顶动态回复
def fetch_top_reply(jump_id, link, UP):
    url = f"https://api.bilibili.com/x/v2/reply/main?csrf=fcce6f152bd72daf7b7ca4e9db826f77&mode=3&oid={jump_id}&pagination_str=%7B%22offset%22:%22%22%7D&plat=1&seek_rpid=0&type=17"
    res = requests.get(url, headers=headers_bili).json()

    if (
        "data" not in res
        or "top_replies" not in res["data"]
        or not res["data"]["top_replies"]
    ):
        return

    reply = res["data"]["top_replies"][0]
    process_reply(reply, link, UP, jump_id)


def process_reply(reply, link, UP, jump_id):
    top_id = reply["rpid_str"]
    msg = reply["content"]["message"]
    ctime = reply["ctime"]

    if msg and isinstance(msg, str):
        msg = msg.replace("\n", " ")[:push_text_len]
    else:
        return

    if m_tg_top[UP["mid"]] == "":
        m_tg_top[UP["mid"]] = top_id
    elif top_id != m_tg_top[UP["mid"]]:
        push(UP["name"] + "置顶", msg, link)
        # push_dynamic(UP["name"], 2, msg, link, ctime)
        m_tg_top[UP["mid"]] = top_id

    monitor_bili_up_reply(
        {
            "oid": jump_id,
            "link": link,
            "root": reply["rpid_str"],
            "rcount": reply["rcount"],
        },
        UP,
    )


m_tg_test = ""


def monitor_bili_follow():
    global m_tg_test, noLogin, headers_bili

    if noLogin:
        return

    url = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?timezone_offset=-480&type=all&page=1&features=itemOpusStyle"
    res = requests.get(url, headers=headers_bili).json()

    if "data" not in res or not res["data"]["items"]:
        return

    item = res["data"]["items"][0]
    basic = item.get("basic", {})
    jump_url = basic.get("jump_url", "")
    desc = item["modules"]["module_dynamic"].get("desc", {})
    name = item["modules"]["module_author"]["name"]
    major = item["modules"]["module_dynamic"].get("major", {})

    # 获取文本内容
    text = desc.get("text", "")
    if "archive" in major:
        archive = major["archive"]
        jump_url = archive.get("jump_url", jump_url)
        text = text or archive.get("title", "")
    elif "ugc_season" in major:
        text = text or major["ugc_season"].get("title", "")

    # 格式化文本
    if text and isinstance(text, str):
        text = text.replace("\n", " ")[:push_text_len]
    else:
        return

    # 处理推送逻辑
    if m_tg_test != item["id_str"]:
        push("关注", text, "https:" + jump_url if jump_url else "")
        m_tg_test = item["id_str"]


# UP置顶回复
start_reply = {}
end_reply = {}


def monitor_bili_up_reply(options, UP):
    global start_reply, end_reply

    mid = UP["mid"]
    if mid not in start_reply:
        start_reply[mid] = {"rpid": -1, "mid": -1}

    if mid not in end_reply:
        end_reply[mid] = {"rpid": -1, "mid": -1}

    end_reply_rpid = int(end_reply[UP["mid"]]["rpid"])
    start_reply_rpid = int(start_reply[UP["mid"]]["rpid"])
    page_size = 20
    # 计算总页数，向上取整
    page_total = math.ceil(options["rcount"] / page_size)

    for page_index in range(page_total, 0, -1):
        time.sleep(1)
        url = f'https://api.bilibili.com/x/v2/reply/reply?oid={options["oid"]}&type=17&root={options["root"]}&ps={page_size}&pn={page_index}&web_location=444.42'
        res = requests.get(url, headers=headers_bili).json()

        if "data" not in res:
            logging.info(UP["name"] + "回复：返回json没包含data字段 ---230行")
            return

        data = res["data"]
        replies = data.get("replies", [])
        root_msg = data["root"]["content"]["message"]

        if root_msg and isinstance(root_msg, str):
            root_msg = root_msg.replace("\n", " ")[0:push_text_len]

        for reply in reversed(replies):
            rpid = reply["rpid_str"]
            mid_reply = reply["mid"]
            msg = reply["content"]["message"]
            rpid_int = int(rpid)

            if page_index == page_total and reply == replies[-1]:
                if end_reply_rpid < rpid_int:
                    end_reply[mid] = {
                        "ctime": reply["ctime"],
                        "mid": mid_reply,
                        "rpid": rpid,
                    }

            if rpid_int <= end_reply_rpid:
                break

            if str(mid_reply) == mid and start_reply_rpid < rpid_int:
                start_reply[mid] = {
                    "ctime": reply["ctime"],
                    "mid": mid_reply,
                    "rpid": rpid,
                }
                text = msg if isinstance(msg, str) else ""
                if text:
                    text = text.replace("\n", " ")[:push_text_len]
                push(
                    UP["name"] + "回复",
                    text,
                    options["link"],
                    f"{root_msg} (评论数量: {options['rcount']})",
                )


# 计算时间差(分钟)
def get_live_time(start_time):
    current_time = datetime.now()
    time_diff = current_time - start_time
    minute = time_diff.seconds // 60 + 1
    return minute


# UP直播
m_live_f = {}
m_live_s = {}
m_live_t = {}


def monitor_bili_up_live_roomId(UP):
    global m_live_f, m_live_s, m_live_t

    # 初始化直播状态
    if UP["mid"] not in m_live_f:
        m_live_f[UP["mid"]] = False

    if UP["mid"] not in m_live_s:
        m_live_s[UP["mid"]] = False

    if UP["mid"] not in m_live_t:
        m_live_t[UP["mid"]] = None

    url = f'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?room_id={UP["roomId"]}'
    live_url = (
        f'https://live.bilibili.com/{UP["roomId"]}?broadcast_type=0&is_room_feed=1'
    )

    headers = {**headers_bili, "Host": "api.live.bilibili.com"}
    res = requests.get(url, headers=headers).json()

    # 检查是否获取到数据
    if "data" not in res:
        if not m_live_s[UP["mid"]]:
            push("异常", UP["name"] + "直播链接rid失效")
            logging.info(UP["name"] + "直播链接rid失效")
            m_live_s[UP["mid"]] = True
        return
    else:
        m_live_s[UP["mid"]] = False

    live = res["data"]
    live_status = live["live_status"]

    # 直播开始
    if live_status == 1 and not m_live_f[UP["mid"]]:
        m_live_t[UP["mid"]] = datetime.now()
        m_live_f[UP["mid"]] = True
        text = "直播开始啦"
        push(UP["name"] + "直播", text, live_url)
        push_dynamic(UP["name"], 3, text, live_url)

    # 直播结束
    elif live_status == 0 and m_live_f[UP["mid"]]:
        live_minute = get_live_time(m_live_t[UP["mid"]])
        m_live_f[UP["mid"]] = False
        text = f"直播结束了(时长: {str(live_minute)}分钟)"
        push(UP["name"] + "直播", text, live_url)
        push_dynamic(UP["name"], 3, text, live_url)


def bili_main():
    global up_list
    # 遍历 up 主列表，监听
    for UP in up_list:
        # 动态监听
        monitor_bili_up_dynamic(UP)
        # 置顶动态监听
        monitor_bili_up_top(UP)
        # 直播监听
        monitor_bili_up_live_roomId(UP)
        time.sleep(12)  # 6 * 2 = 12
