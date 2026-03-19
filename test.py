import requests
import json
import os
from urllib.parse import urlparse, parse_qs

# --- 1. 环境变量 (GitHub Secrets) ---
APP_TOKEN = os.environ.get("WX_APP_TOKEN")
MY_UID = os.environ.get("WX_MY_UID")

# --- 2. 核心路径配置 ---
WECHAT_API = 'http://wxpusher.zjiecode.com/api/send/message'
API_URL = "https://www.szggzy.com/cms/api/v1/rhgw/project/detail"
CONFIG_FILE = "config.json"       # 小白在网页改的文件
CACHE_FILE = "project_status.json" # 记忆文件

def get_content_id_from_url(url):
    """从输入的网址中精准提取 contentId"""
    try:
        query = urlparse(url).query
        return parse_qs(query).get('contentId', [None])[0]
    except:
        return None

def load_config_url():
    """从 config.json 读取小白在网页上填写的网址"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            # 读取网页同步过来的新地址
            return json.load(f).get("target_url")
    return None

def send_wechat(msg_title, msg_content):
    """微信推送函数"""
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
    """核心监控逻辑"""
    content_id = get_content_id_from_url(target_url)
    if not content_id:
        print(f"!!! 无法从网址提取 ID: {target_url}")
        return

    print(f"--- 监控任务启动 (目标ID: {content_id}) ---")
    headers = {"User-Agent": "Mozilla/5.0...", "X-Requested-With": "XMLHttpRequest"}
    params = {"contentId": content_id, "siteName": "jsgc"}
    
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=15)
        res_data = response.json().get('data', {})
        n_list = res_data.get('noticeList', [])
        
        project_name = res_data.get("project", {}).get("projectName") or "招标项目"
        current_ids = set([item['noticeId'] for item in n_list])
        
        # 读取旧记忆
        old_ids = set()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                try: old_ids = set(json.load(f))
                except: pass

        # 发现新公告
        new_ids = current_ids - old_ids
        if new_ids:
            print(f"🔔 发现 {len(new_ids)} 条新动态！")
            details = [f"【{n['noticeTypeName']}】\n标题：{n['noticeTitle']}" for n in n_list if n['noticeId'] in new_ids]
            send_wechat("项目更新提醒", f"项目：{project_name}\n\n" + "\n\n".join(details))
            
            # 更新记忆，防止重复推送
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(list(current_ids), f, ensure_ascii=False)
        else:
            print(f">>> 暂无新变动 (当前已掌握 {len(current_ids)} 条信息)")
            
    except Exception as e:
        print(f">>> 运行异常: {e}")

if __name__ == "__main__":
    # 关键：先看“情报中心”有没有新指示
    current_url = load_config_url()
    if current_url:
        monitor(current_url)
    else:
        print(">>> 错误：未找到有效的 config.json")
