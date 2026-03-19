import streamlit as st
import requests
import base64
import json
import time

# --- 基础配置 ---
GITHUB_REPO = "thethe-github/app_monitor" # 请确保这是你真实的仓库名
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

st.set_page_config(page_title="多项目监控中心", page_icon="⚙️", layout="wide")

# --- 初始化会话状态 (Session State) ---
# 这样即便 GitHub 还没更新完，本地界面也会立刻显示变化
if 'urls' not in st.session_state:
    st.session_state.urls = []
if 'file_sha' not in st.session_state:
    st.session_state.file_sha = None

def sync_from_github():
    """从 GitHub 同步最新配置到本地状态"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(api_url, headers=headers).json()
    if "content" in res:
        content = base64.b64decode(res["content"]).decode('utf-8')
        st.session_state.urls = json.loads(content).get("urls", [])
        st.session_state.file_sha = res.get("sha")

def push_to_github(new_urls):
    """将本地修改同步到 GitHub"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    new_content = base64.b64encode(json.dumps({"urls": new_urls}, indent=2).encode()).decode()
    payload = {
        "message": "Update URL list via UI",
        "content": new_content,
        "sha": st.session_state.file_sha
    }
    res = requests.put(api_url, json=payload, headers=headers)
    if res.status_code == 200:
        st.session_state.file_sha = res.json().get("content", {}).get("sha")
    return res

# 首次运行同步一次
if not st.session_state.file_sha:
    sync_from_github()

# --- UI 界面 ---
st.title("🚀 项目监控配置中心")
st.caption("修改将实时同步至 GitHub 后台工人")

# 1. 显示当前清单
st.subheader("📋 当前监控清单")
if not st.session_state.urls:
    st.info("目前没有正在监控的项目。")
else:
    for i, url in enumerate(st.session_state.urls):
        cols = st.columns([0.8, 0.2])
        cols[0].code(url, language="text")
        if cols[1].button("🗑️ 删除", key=f"del_{i}"):
            # 先改本地，立刻见效
            st.session_state.urls.pop(i)
            # 后台同步
            push_to_github(st.session_state.urls)
            st.rerun()

st.divider()

# 2. 添加新监控
st.subheader("➕ 添加新监控")
new_url = st.text_input("粘贴新的招标详情页网址：", key="input_url")

if st.button("确认添加", type="primary"):
    if new_url and new_url not in st.session_state.urls:
        # 核心优化：先更新本地状态
        st.session_state.urls.append(new_url)
        
        # 异步同步给 GitHub
        with st.spinner('正在同步至云端...'):
            res = push_to_github(st.session_state.urls)
            
            if res.status_code == 200:
                st.success("✅ 添加成功！后台已开始排期。")
                time.sleep(0.5) # 给用户一个看反馈的时间
                st.rerun()
            else:
                st.error(f"同步失败: {res.json().get('message')}")
    elif new_url in st.session_state.urls:
        st.warning("该网址已在清单中。")
