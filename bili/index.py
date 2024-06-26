import requests
import time
from datetime import datetime
import copy  
import logging
from script.push import push,push_dynamic
push_text_len = 50
bili_moda_mid = '525121722'
bili_live_room_id = '23229268'
bili_moda_opus_link = 'https://www.bilibili.com/opus/'
live_start_time = None
noLogin = False
headers_bili={
    'Accept': 'application/json, text/plain, */*',
    'Connection': 'keep-alive',
    'Cookie': '',
    'Host': 'api.bilibili.com',
    'Origin': 'https://space.bilibili.com',
    'Referer': 'https://space.bilibili.com/525121722/dynamic',
    'sec-ch-ua': '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57'
}
# 莫大动态
m_tg = ''
def monitor_bili_moda_dynamic():
    global m_tg
    global noLogin
    global headers_bili
    global bili_moda_mid
    jump_url = ''
    ctime = ''
    url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={bili_moda_mid}'
    res = requests.get(url,headers=headers_bili).json()
    if 'data' not in res:
      return
    list = res['data']['items'][0]
    if 'module_tag' in list['modules']:
      m_module_tag = list['modules']['module_tag']
      if(m_module_tag['text']=='置顶'):
          list = res['data']['items'][1]
    id = list['id_str']
    jump_url = bili_moda_opus_link + id
    text = list['modules']['module_dynamic']['desc']
    module_author = list['modules']['module_author']
    ctime = module_author['pub_ts']
    if text:
        text = text['text']
    else:
        text = list['modules']['module_dynamic']['major']
        if 'archive' in text:
            text = text['archive']['title']
        elif 'ugc_season' in text:
            text = text['ugc_season']['title']
        elif 'opus' in text:
           opus = text['opus']       
           if 'summary' in opus:
              text = opus['summary']['text']           
    if text and isinstance(text,str):
      text = text.replace('\n',' ')[0:push_text_len]
    else:
      logging.info('莫大动态：text类型错误')
      return
    if(m_tg == ''):
        m_tg = id
    elif(m_tg != id):
        push('动态',text,jump_url)
        push_dynamic(1,text,jump_url,ctime)
        m_tg = id
# 莫大置顶
m_tg_top = ''
def monitor_bili_moda_top():
    global m_tg_top
    global noLogin
    global headers_bili
    global bili_moda_mid
    if noLogin:
        return
    url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={bili_moda_mid}'
    res = requests.get(url,headers=headers_bili).json()
    if 'data' not in res:
      logging.info('置顶：返回json没包含data字段 ---86行')
      return
    list = res['data']['items']
    jump_id = ''
    link=''
    for i in range(len(list)):
        if 'module_tag' in list[i]['modules']:
          m_module_tag = list[i]['modules']['module_tag']
          if(m_module_tag['text']=='置顶'):
            id_str = list[i]['id_str']
            jump_id = id_str
            link = bili_moda_opus_link + jump_id
    if bool(jump_id):
        url = f'https://api.bilibili.com/x/v2/reply/main?csrf=fcce6f152bd72daf7b7ca4e9db826f77&mode=3&oid={jump_id}&pagination_str=%7B%22offset%22:%22%22%7D&plat=1&seek_rpid=0&type=17'
        res = requests.get(url,headers=headers_bili).json()
        if 'data' not in res:
          return
        data = res['data']
        if 'top_replies' not in data:
          return
        if len(data['top_replies']) < 1:
          return
        reply = data['top_replies'][0]
        top_id = reply['rpid_str']
        msg = reply['content']['message']
        rcount = reply['rcount']
        rpid = reply['rpid_str']
        ctime = reply['ctime']
        if msg and isinstance(msg,str):
            msg = msg.replace('\n',' ')[0:push_text_len]
        else:
          return
        if m_tg_top == '':
            m_tg_top = top_id
        elif top_id != m_tg_top:
            top_msg = msg
            push('置顶',top_msg, link)
            push_dynamic(2,top_msg,link,ctime)
            m_tg_top = top_id
        monitor_bili_moda_reply({'oid':jump_id,'link':link,'root':rpid,'rcount':rcount})
    else:
        push('异常','bili cookie失效,请重新登录')
        logging.info('bili cookie失效,请重新登录')
        noLogin = True

m_tg_test = ''
def monitor_bili_follow():
    global m_tg_test
    global noLogin
    global headers_bili
    jump_url = ''
    text = ''
    if noLogin:
        return
    url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?timezone_offset=-480&type=all&page=1&features=itemOpusStyle'
    # res = requests.get(url,headers=headers,verify=False).json()
    res = requests.get(url,headers=headers_bili).json()
    if 'data' not in res:
      return
    list = res['data']['items']
    id = list[0]['id_str']
    basic = list[0]['basic']
    if 'jump_url' in basic:
      jump_url = basic['jump_url']
    desc = list[0]['modules']['module_dynamic']['desc']
    name =list[0]['modules']['module_author']['name']
    major = list[0]['modules']['module_dynamic']['major']
    if desc:
        text = desc['text']
    if major:
        if 'archive' in major:
            archive =  major['archive']
            if 'jump_url' in  archive:
               jump_url = archive['jump_url']
            if not text:
              text = archive['title']
        if 'ugc_season' in major and not text:
            text = major['ugc_season']['title']

    if text and isinstance(text,str):
      text = text.replace('\n',' ')[0:push_text_len]
    else:
        return
    # logging.info('关注最新动态')
    if(m_tg_test == ''):
        m_tg_test = id
    elif(m_tg_test != id):
        if jump_url:
           push('关注', text,'https:'+jump_url)
        else:
           push('关注', text)
        m_tg_test = id

# 直播
m_live_status = False
m_live_flag = False
def monitor_bili_moda_live():
    global m_live_flag
    global m_live_status
    global live_start_time
    global bili_moda_mid
    url = f'https://api.bilibili.com/x/space/wbi/acc/info?mid={bili_moda_mid}'
    res = requests.get(url,headers=headers_bili).json()
    if 'data' not in res:
        if not m_live_status:
            push('异常','莫大直播链接rid失效')
            logging.info('莫大直播链接rid失效')
            m_live_status = True
        return
    else:
        if m_live_status:
            m_live_status = False
    live = res['data']['live_room']
    if live:
        live_status = live['liveStatus']
        live_title = live['title']
        live_url = live['url']
        if(not m_live_flag and live_status == 1):
            live_start_time = datetime.now()
            m_live_flag = True
            push('直播','莫大直播开始啦--'+live_title,live_url)
        if(live_status == 0 and m_live_flag):
            live_minute = get_live_time(live_start_time) 
            m_live_flag = False
            push('直播','莫大直播结束了--'+live_title+f'(直播时长: {str(live_minute)}分钟)')

# 回复
start_reply={'rpid':-1,'mid':-1}
end_reply={'rpid':-1,'mid':-1}
def monitor_bili_moda_reply(options):
  global start_reply
  global end_reply
  end_reply_rpid = int(end_reply['rpid'])
  start_reply_rpid = int(start_reply['rpid'])
  break_flag = False
  pageSize = 20
  pageTotal = options['rcount'] // pageSize + 1
  for pageIndex in range(pageTotal,0,-1):
    time.sleep(1)
    url = f'https://api.bilibili.com/x/v2/reply/reply?oid={options["oid"]}&type=17&root={options["root"]}&ps={pageSize}&pn={pageIndex}&web_location=444.42'
    res = requests.get(url,headers=headers_bili).json()
    if 'data' not in res:
      return
    # logging.info('回复：'+ str('数量 ' +options["rcount"]+'---229行'))
    data = res['data']
    replies = data['replies']
    root = data['root']
    root_msg = root['content']['message']
    if root_msg and isinstance(root_msg,str):
      root_msg = root_msg.replace('\n',' ')[0:push_text_len]
    le = len(replies)-1
    for i in range(le,-1,-1):
      current_start_reply_rpid = int(start_reply['rpid'])
      reply = replies[i]
      rpid = reply['rpid_str']
      mid = reply['mid']
      msg = reply['content']['message']
      rpid_int = int(rpid)
      if pageIndex == pageTotal and i == le:
        if end_reply_rpid < rpid_int:
          ctime = reply['ctime']
          end_reply = {'ctime':ctime,'mid':mid,'rpid':rpid}
      if rpid_int <= end_reply_rpid or end_reply_rpid == -1:
        break_flag = True
        break
      if str(mid) == bili_moda_mid and start_reply_rpid < rpid_int:
        ctime = reply['ctime']
        if current_start_reply_rpid < rpid_int:
          start_reply = {'ctime':ctime,'mid':mid,'rpid':rpid}
        text = msg
        if text and isinstance(text,str):
          text = text.replace('\n',' ')[0:push_text_len]
        push('回复',text,options['link'],root_msg+f'(评论数量: {options["rcount"]})')

    if(break_flag):
      break

# 计算时间差(分钟)
def get_live_time(start_time):
    current_time = datetime.now()
    time_diff = current_time - start_time
    minute = time_diff.seconds // 60 + 1
    return minute

# 直播
def monitor_bili_moda_live_roomId():
    global m_live_flag
    global m_live_status
    global live_start_time
    global bili_live_room_id
    url= f'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?room_id={bili_live_room_id}'
    live_url = f'https://live.bilibili.com/{bili_live_room_id}?broadcast_type=0&is_room_feed=1'
    headers = copy.deepcopy(headers_bili)
    headers['Host'] = "api.live.bilibili.com"
    res = requests.get(url,headers=headers).json()
    if 'data' not in res:
        if not m_live_status:
            push('异常','莫大链接rid失效')
            logging.info('莫大直播链接rid失效')
            m_live_status = True
        return
    else:
        if m_live_status:
            m_live_status = False
    live = res['data']
    if live:
        live_status = live['live_status']
        live_time = live['live_time']
        if(not m_live_flag and live_status == 1):
            live_start_time = datetime.now()
            m_live_flag = True
            text = '莫大直播开始啦'
            push('直播',text,live_url)
            push_dynamic(3,text,live_url)
        if(live_status == 0 and m_live_flag):
            live_minute = get_live_time(live_start_time) 
            m_live_flag = False
            text = f'莫大直播结束了(时长: {str(live_minute)}分钟)'
            push('直播',text,live_url)
            push_dynamic(3,text,live_url)