import requests
import json
import os
from urllib.parse import urlparse, parse_qs

# --- 环境变量 (GitHub Secrets) ---
APP_TOKEN = os.environ.get("WX_APP_TOKEN")
MY_UID = os.environ.get("WX_MY_UID")

# --- 路径配置 ---
WECHAT_API = 'http://wxpusher.zjiecode.com/api/send/message'
API_URL = "https://www.szggzy.com/cms/api/v1/rhgw/project/detail"
CONFIG_FILE = "config.json"

def get_content_id(url):
    try:
        query = urlparse(url).query
        return parse_qs(query).get('contentId', [None])[0]
    except: return None

def monitor_single_project(url):
    """针对单个 URL 执行监控逻辑"""
    content_id = get_content_id(url)
    if not content_id: return
    
    # 每个项目拥有独立的记忆文件，防止混淆
    cache_file = f"status_{content_id}.json"
    
    print(f"\n>>> 正在检查项目: {content_id}")
    headers = {"User-Agent": "Mozilla/5.0...", "X-Requested-With": "XMLHttpRequest"}
    params = {"contentId": content_id, "siteName": "jsgc"}
    
    try:
        res = requests.get(API_URL, params=params, headers=headers, timeout=15).json()
        res_data = res.get('data', {})
        n_list = res_data.get('noticeList', [])
        project_name = res_data.get("project", {}).get("projectName") or "未知项目"
        
        current_ids = set([item['noticeId'] for item in n_list])
        old_ids = set()
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f: old_ids = set(json.load(f))
        
        new_ids = current_ids - old_ids
        if new_ids:
            # 整理并推送更新
            details = [f"【{n['noticeTypeName']}】\n标题：{n['noticeTitle']}" for n in n_list if n['noticeId'] in new_ids]
            msg = f"项目：{project_name}\nID: {content_id}\n\n" + "\n\n".join(details)
            
            # 发送微信推送 (复用之前的 send_wechat 逻辑)
            send_wechat("发现新动态", msg)
            
            with open(cache_file, "w") as f: json.dump(list(current_ids), f)
            print(f"🔔 {content_id} 发现更新并已推送。")
        else:
            print(f"✅ {content_id} 暂无变动。")
    except Exception as e:
        print(f"❌ {content_id} 运行异常: {e}")

if __name__ == "__main__":
    # 核心改动：从读取单个 URL 变为读取 URL 列表
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            url_list = json.load(f).get("urls", [])
        
        print(f"=== 启动多任务监控，共 {len(url_list)} 个项目 ===")
        for url in url_list:
            monitor_single_project(url)
    else:
        print("未找到 config.json 配置文件。")
