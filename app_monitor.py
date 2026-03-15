import streamlit as st
import requests
import json
import os
import time
from urllib.parse import urlparse, parse_qs

# --- 核心配置 ---
WECHAT_API = 'http://wxpusher.zjiecode.com/api/send/message'
API_URL = "https://www.szggzy.com/cms/api/v1/rhgw/project/detail"

# 页面基础配置
st.set_page_config(page_title="招标项目监控", page_icon="🔍")

# --- 核心逻辑函数 ---

def get_content_id(url):
    """从网址解析 ID"""
    try:
        query = urlparse(url).query
        return parse_qs(query).get('contentId', [None])[0]
    except: return None

def send_wechat(token, uid, title, content):
    """微信推送函数"""
    data = {
        "appToken": token,
        "content": content,
        "summary": title,
        "contentType": 1,
        "uids": [uid],
    }
    try:
        # 在本地运行建议加入 timeout 防止卡死
        requests.post(url=WECHAT_API, json=data, timeout=20)
    except: pass

# --- UI 界面 ---

st.title("🔍 招标项目监控助手")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 凭证设置")
    app_token = st.text_input("WxPusher AppToken", value="xxx", type="password")
    my_uid = st.text_input("你的个人 UID", value="xxx")

target_url = st.text_input("📌 请粘贴项目详情页网址：")
interval_min = st.number_input("⏰ 监控频率 (分钟)", min_value=1, value=30)

if st.button("🚀 启动监控"):
    content_id = get_content_id(target_url)
    
    if not content_id:
        st.error("❌ 无法识别网址中的 contentId，请检查格式。")
    else:
        st.success(f"已锁定项目 {content_id}，正在后台运行...")
        
        # 使用 empty() 创建两个可以被不断刷新覆盖的“位置”
        status_display = st.empty()  # 用于显示“最后检查时间”
        message_display = st.empty() # 用于显示“有没有新公告”
        
        cache_file = f"status_{content_id}.json"
        
        while True:
            now_str = time.strftime('%H:%M:%S')
            # 模拟 test.py 的请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }
            params = {"contentId": content_id, "siteName": "jsgc"}
            
            try:
                # 1. 获取数据
                res = requests.get(API_URL, params=params, headers=headers, timeout=15).json()
                res_data = res.get('data', res)
                n_list = res_data.get('noticeList', [])
                project_name = res_data.get("project", {}).get("projectName") or "未知项目"
                
                # 2. 提取 ID 集合
                current_notices = {item['noticeId']: item for item in n_list}
                current_ids = set(current_notices.keys())
                
                # 3. 读取旧缓存
                old_ids = set()
                if os.path.exists(cache_file):
                    with open(cache_file, "r", encoding="utf-8") as f:
                        try: old_ids = set(json.load(f))
                        except: pass
                
                # 4. 比对新变动
                new_ids = current_ids - old_ids
                
                if new_ids:
                    # 5. 拼接完整推送内容
                    push_details = []
                    for nid in new_ids:
                        item = current_notices[nid]
                        detail = f"【{item.get('noticeTypeName')}】\n标题：{item.get('noticeTitle')}\n时间：{item.get('publishTime')}"
                        push_details.append(detail)
                    
                    msg_full = f"项目：{project_name}\n\n" + "\n\n".join(push_details)
                    send_wechat(app_token, my_uid, "招标更新提醒", msg_full)
                    
                    # 更新缓存
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(list(current_ids), f, ensure_ascii=False)
                    
                    status_display.info(f"💡 最后运行时间：{now_str}")
                    message_display.warning(f"🔔 发现 {len(new_ids)} 条更新，已推送到微信！")
                else:
                    status_display.info(f"💡 最后运行时间：{now_str}")
                    message_display.write(f"💤 暂无变动（当前共 {len(current_ids)} 条公告）")
            
            except Exception as e:
                status_display.error(f"发生错误：{e}")
            
            time.sleep(interval_min * 60) #
