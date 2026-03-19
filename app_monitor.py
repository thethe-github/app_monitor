import streamlit as st
import requests
import base64
import json

# --- 基础配置 ---
GITHUB_REPO = "thethe-github/app_monitor" 
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

st.set_page_config(page_title="多项目监控中心", page_icon="🚀", layout="wide")

# --- 初始化状态 ---
if 'urls' not in st.session_state:
    st.session_state.urls = []
if 'file_sha' not in st.session_state:
    st.session_state.file_sha = None

def sync_from_github():
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(api_url, headers=headers).json()
    if "content" in res:
        content = base64.b64decode(res["content"]).decode('utf-8')
        st.session_state.urls = json.loads(content).get("urls", [])
        st.session_state.file_sha = res.get("sha")

def push_to_github(new_urls):
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    new_content = base64.b64encode(json.dumps({"urls": new_urls}, indent=2).encode()).decode()
    payload = {"message": "Update URL list", "content": new_content, "sha": st.session_state.file_sha}
    res = requests.put(api_url, json=payload, headers=headers)
    if res.status_code == 200:
        st.session_state.file_sha = res.json().get("content", {}).get("sha")
    return res

if not st.session_state.file_sha:
    sync_from_github()

# --- 界面展示 ---
st.title("🚀 项目监控配置中心")

# 1. 监控清单
st.subheader("📋 当前监控清单")
if not st.session_state.urls:
    st.info("目前没有正在监控的项目。")
else:
    for i, url in enumerate(st.session_state.urls):
        cols = st.columns([0.85, 0.15])
        cols[0].code(url, language="text")
        if cols[1].button("🗑️ 删除", key=f"del_{i}"):
            st.session_state.urls.pop(i)
            push_to_github(st.session_state.urls)
            st.rerun()

st.divider()

# 2. 添加监控 (使用 Form 解决报错并实现自动清空)
st.subheader("➕ 添加新项目")

# clear_on_submit 是灵魂，点击按钮后输入框自动归零
with st.form("my_form", clear_on_submit=True):
    new_url = st.text_input("粘贴招标详情页网址：")
    submitted = st.form_submit_button("确认添加", type="primary")
    
    if submitted:
        if new_url:
            if new_url not in st.session_state.urls:
                # 逻辑处理
                st.session_state.urls.append(new_url)
                
                with st.spinner('同步至云端...'):
                    res = push_to_github(st.session_state.urls)
                    if res.status_code == 200:
                        st.toast("✅ 添加成功，已同步！")
                        st.rerun() # 刷新上方列表
                    else:
                        st.error(f"同步失败: {res.status_code}")
            else:
                st.warning("该项目已在监控中。")
        else:
            st.error("请输入有效的网址。")

st.caption("提示：由于 GitHub API 延迟，若列表未更新请手动刷新页面。")
