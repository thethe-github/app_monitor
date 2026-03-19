import requests
import json
import os
from urllib.parse import urlparse, parse_qs

# --- 1. 环境变量读取 (GitHub Secrets) ---
APP_TOKEN = os.environ.get("WX_APP_TOKEN")
MY_UID = os.environ.get("WX_MY_UID")

# --- 2. 核心路径配置 ---
WECHAT_API = 'http://wxpusher.zjiecode.com/api/send/message'
API_URL = "https://www.szggzy.com/cms/api/v1/rhgw/project/detail"
CONFIG_FILE = "config.json"
CACHE_FILE = "project_status.json"

def get_content_id_from_url(url):
    """从输入的网址中精准提取 contentId"""
    try:
        query = urlparse(url).query
        return parse_qs(query).get('contentId', [None])[0]
    except:
        return None

def load_config_url():
    """从配置文件读取小白设置的网址"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("target_url")
    return None

def send_wechat(msg_title, msg_content):
    """微信推送逻辑"""
    if not APP_TOKEN or not MY_UID:
        print(">>> 错误：未读取到环境变量")
        return
    data = {"appToken": APP_TOKEN, "content": msg_content, "summary": msg_title, "contentType": 1, "uids": [MY_UID]}
    try:
        res = requests.post(url=WECHAT_API, json=data, timeout=20)
        print(f">>> 微信推送结果: {res.json().get('msg')}")
    except Exception as e:
        print(f">>> 推送异常: {e}")

def monitor(target_url):
    """根据传入的 URL 执行监控"""
    content_id = get_content_id_from_url(target_url)
    if not content_id:
        print("!!! 配置文件中的网址格式不正确，无法提取 ID")
        return

    print(f"--- 监控任务启动 (项目ID: {content_id}) ---")
    headers = {
        "User-Agent": "Mozilla/5.0...", 
        "X-Requested-With": "XMLHttpRequest"
    }
    params = {"contentId": content_id, "siteName": "jsgc"}
    
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=15)
        data = response.json()
        
        # 数据提取与比对逻辑 (保留你原来的全步骤监控代码)
        res_data = data.get('data', data)
        n_list = res_data.get('noticeList', [])
        if not n_list:
            print(">>> 暂无公告数据。")
            return

        project_name = res_data.get("project", {}).get("projectName") or "监控项目"
        current_ids = set([item['noticeId'] for item in n_list])
        
        # 读取旧状态
        old_ids = set()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                try: old_ids = set(json.load(f))
                except: pass

        new_ids = current_ids - old_ids
        if new_ids:
            # 整理新动态并推送
            details = [f"【{n['noticeTypeName']}】\n标题：{n['noticeTitle']}" for n in n_list if n['noticeId'] in new_ids]
            send_wechat("项目更新提醒", f"项目：{project_name}\n\n" + "\n\n".join(details))
            
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(list(current_ids), f, ensure_ascii=False)
        else:
            print(f">>> 暂无变动 (共 {len(current_ids)} 条历史条目)")
            
    except Exception as e:
        print(f">>> 运行异常: {e}")

if __name__ == "__main__":
    current_url = load_config_url()
    if current_url:
        monitor(current_url)
    else:
        print(">>> 错误：未找到有效的 config.json 配置文件。")
