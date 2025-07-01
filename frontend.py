import streamlit as st
import requests

# FastAPI 后端服务的地址
FASTAPI_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RAG 问答机器人", page_icon="🤖")

st.title("🤖 员工手册 RAG 问答机器人")
st.markdown("---")

# --- 新增：测试后端连接 ---
st.sidebar.header("后端连接状态")
try:
    response = requests.get(FASTAPI_URL, proxies={'http': None, 'https': None})
    response.raise_for_status()
    st.sidebar.success(f"成功连接到后端：{response.json().get('message', '未知消息')}")
except requests.exceptions.ConnectionError as e:
    st.sidebar.error(f"无法连接到后端：{e}")
except requests.exceptions.RequestException as e:
    st.sidebar.error(f"后端连接错误：{e}")
# --- 新增结束 ---

# 用户输入问题
user_question = st.text_area("请输入您的问题：", height=100, placeholder="例如：产品的主要功能是什么？")

if st.button("提问"):
    if user_question:
        with st.spinner("正在思考中..."):
            try:
                # --- 添加调试信息 ---
                print(f"[前端] 尝试连接后端：{FASTAPI_URL}/ask")
                print(f"[前端] 发送的问题：{user_question}")
                # --- 调试信息结束 ---

                # 调用 FastAPI 后端 API
                response = requests.post(f"{FASTAPI_URL}/ask", json={"question": user_question}, proxies={'http': None, 'https': None})
                response.raise_for_status() # 检查 HTTP 错误
                
                result = response.json()
                # --- 添加调试信息 ---
                print(f"[前端] 收到后端原始响应：{result}")
                # --- 调试信息结束 ---
                answer = result.get("answer", "抱歉，未能找到答案。")
                source_documents = result.get("source_documents", [])

                st.subheader("回答：")
                st.write(answer)

                if source_documents:
                    st.subheader("参考来源：")
                    for doc in source_documents:
                        st.markdown(f"- **文件:** {doc.get('source', '未知')} (页码: {doc.get('page', '未知')})")

            except requests.exceptions.ConnectionError as e:
                # --- 添加调试信息 ---
                print(f"捕获到连接错误：{e}")
                # --- 调试信息结束 ---
                st.error(f"错误：无法连接到后端服务。请确保 FastAPI 服务正在运行在 {FASTAPI_URL}。")
            except requests.exceptions.RequestException as e:
                # --- 添加调试信息 ---
                print(f"捕获到请求错误：{e}")
                # --- 调试信息结束 ---
                st.error(f"请求后端服务时发生错误：{e}")
            except Exception as e:
                # --- 添加调试信息 ---
                print(f"捕获到未知错误：{e}")
                # --- 调试信息结束 ---
                st.error(f"发生未知错误：{e}")
    else:
        st.warning("请输入您的问题！")

st.markdown("---")
st.info("请确保后端 FastAPI 服务 (uvicorn main:app --reload) 正在运行。")