import requests
import json
import os
from urllib.parse import urlparse, parse_qs

# --- 1. 环境变量 (GitHub Secrets) ---
APP_TOKEN = os.environ.get("WX_APP_TOKEN")
MY_UID = os.environ.get("WX_MY_UID")

# --- 2. 路径配置 ---
WECHAT_API = 'http://wxpusher.zjiecode.com/api/send/message'
API_URL = "https://www.szggzy.com/cms/api/v1/rhgw/project/detail"
CONFIG_FILE = "config.json"

def get_content_id(url):
    """解析网址获取 ID"""
    try:
        query = urlparse(url).query
        return parse_qs(query).get('contentId', [None])[0]
    except: 
        return None

def send_wechat(msg_title, msg_content):
    """微信推送函数"""
    if not APP_TOKEN or not MY_UID:
        print(">>> 错误：未读取到环境变量 (WX_APP_TOKEN 或 WX_MY_UID)")
        return
    data = {
        "appToken": APP_TOKEN,
        "content": msg_content,
        "summary": msg_title,
        "contentType": 1,
        "uids": [MY_UID],
    }
    try:
        res = requests.post(url=WECHAT_API, json=data, timeout=20)
        print(f">>> 微信推送结果: {res.json().get('msg')}")
    except Exception as e:
        print(f">>> 推送异常: {e}")

def monitor_single_project(url):
    """针对单个 URL 执行监控逻辑"""
    content_id = get_content_id(url)
    if not content_id: 
        print(f"!!! 无法解析网址 ID: {url}")
        return
    
    # 每个项目独立的缓存文件
    cache_file = f"status_{content_id}.json"
    
    print(f"\n>>> 正在检查项目: {content_id}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    params = {"contentId": content_id, "siteName": "jsgc"}
    
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=15)
        res_data = response.json().get('data', {})
        n_list = res_data.get('noticeList', [])
        project_name = res_data.get("project", {}).get("projectName") or "未知项目"
        
        current_ids = set([item['noticeId'] for item in n_list])
        
        # 读取旧记忆
        old_ids = set()
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                try:
                    old_ids = set(json.load(f))
                except:
                    pass
        
        # 比对新变动
        new_ids = current_ids - old_ids
        if new_ids:
            print(f"🔔 发现 {len(new_ids)} 条新动态！")
            details = [f"【{n['noticeTypeName']}】\n标题：{n['noticeTitle']}\n时间：{n['publishTime']}" for n in n_list if n['noticeId'] in new_ids]
            msg = f"项目：{project_name}\nID: {content_id}\n\n" + "\n\n".join(details)
            
            # 这里现在可以正常调用 send_wechat 了
            send_wechat("发现招标更新", msg)
            
            # 更新该项目的独立记忆
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(list(current_ids), f, ensure_ascii=False)
        else:
            print(f"✅ {content_id} 暂无变动。")
            
    except Exception as e:
        print(f"❌ {content_id} 运行异常: {e}")

if __name__ == "__main__":
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            url_list = json.load(f).get("urls", [])
        
        if not url_list:
            print(">>> 清单为空，请先在网页端添加网址。")
        else:
            print(f"=== 启动多任务轮询，共 {len(url_list)} 个项目 ===")
            for url in url_list:
                monitor_single_project(url)
    else:
        print(">>> 错误：未找到 config.json 配置文件。")
