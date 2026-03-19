import streamlit as st
import requests
import base64
import json

# --- 基础配置 ---
# 请确保这里的仓库路径完全正确
GITHUB_REPO = "thethe-github/monitor"
# GITHUB_TOKEN 需要你在 Streamlit Cloud 后台的 Secrets 中添加
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] 

st.set_page_config(page_title="监控配置中心", page_icon="⚙️")
st.title("⚙️ 项目监控配置中心")
st.write("在这里修改网址，GitHub 后台工人会自动每小时打卡检查。")

# 获取当前配置（为了展示给用户看）
def get_current_config():
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(api_url, headers=headers).json()
    if "content" in res:
        content = base64.b64decode(res["content"]).decode('utf-8')
        return json.loads(content).get("target_url"), res.get("sha")
    return "", None

current_url, file_sha = get_current_config()

st.info(f"当前正在监控：\n{current_url if current_url else '未设置'}")

new_url = st.text_input("🔗 粘贴新的监控网址：", placeholder="https://www.szggzy.com/...")

if st.button("💾 保存并立即生效"):
    if not new_url:
        st.warning("请输入网址后再保存。")
    else:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/config.json"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        # 准备新内容
        new_config = {"target_url": new_url}
        new_content_encoded = base64.b64encode(json.dumps(new_config).encode()).decode()

        payload = {
            "message": "Update target URL via Streamlit UI",
            "content": new_content_encoded,
            "sha": file_sha # 必须提供 SHA 才能更新文件
        }
        
        update_res = requests.put(api_url, json=payload, headers=headers)
        
        if update_res.status_code == 200:
            st.success("✅ 配置已同步！GitHub Actions 将在下一周期执行新任务。")
            st.balloons()
        else:
            st.error(f"❌ 同步失败：{update_res.json().get('message')}")
