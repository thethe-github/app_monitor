import streamlit as st
import requests
import base64
import json

# --- 基础配置 ---
GITHUB_REPO = "thethe-github/monitor"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

st.set_page_config(page_title="多项目监控中心", page_icon="⚙️")
st.title("⚙️ 项目监控配置中心 (多任务版)")

def get_github_config():
    """获取云端配置列表"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(api_url, headers=headers).json()
    if "content" in res:
        content = base64.b64decode(res["content"]).decode('utf-8')
        return json.loads(content).get("urls", []), res.get("sha")
    return [], None

def update_github_config(new_urls, sha):
    """同步更新到 GitHub"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    new_content = base64.b64encode(json.dumps({"urls": new_urls}, indent=2).encode()).decode()
    payload = {"message": "Update URL list via UI", "content": new_content, "sha": sha}
    return requests.put(api_url, json=payload, headers=headers)

# --- 核心 UI 逻辑 ---
urls, file_sha = get_github_config()

st.subheader("📋 当前监控清单")
if not urls:
    st.info("目前没有正在监控的项目。")
else:
    # 遍历列表，显示网址及删除按钮
    for i, url in enumerate(urls):
        col1, col2 = st.columns([8, 2])
        col1.code(url, language="text")
        if col2.button("🗑️ 删除", key=f"del_{i}"):
            urls.pop(i)
            res = update_github_config(urls, file_sha)
            if res.status_code == 200:
                st.rerun() # 刷新页面

st.markdown("---")
st.subheader("➕ 添加新监控")
new_url = st.text_input("粘贴新的招标详情页网址：")
if st.button("确认添加"):
    if new_url and new_url not in urls:
        urls.append(new_url)
        res = update_github_config(urls, file_sha)
        if res.status_code == 200:
            st.success("✅ 已添加并同步！")
            st.balloons()
            st.rerun()
    elif new_url in urls:
        st.warning("该网址已在监控清单中。")
