import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
# 移除重排器相关导入
# from langchain.retrievers import ContextualCompressionRetriever
# from langchain_community.document_compressors import SentenceTransformerRerank

# 加载环境变量
load_dotenv()

# 检查 API Key
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key or google_api_key == 'YOUR_GOOGLE_API_KEY':
    raise ValueError("请在 .env 文件中设置您的 GOOGLE_API_KEY")

# 定义常量
PERSIST_DIR = "db"

# 初始化 FastAPI 应用
app = FastAPI()

# 定义请求体
class QuestionRequest(BaseModel):
    question: str

qa_chain = None

@app.on_event("startup")
def startup_event():
    """应用启动时加载资源"""
    global qa_chain
    print("[后端] 正在加载资源 (使用 Google API)...")

    # 检查数据库目录
    print("[后端] 检查数据库目录...")
    if not os.path.exists(PERSIST_DIR):
        raise FileNotFoundError(f"错误：数据库目录 '{PERSIST_DIR}' 不存在。请先运行 ingest.py。")
    print("[后端] 数据库目录存在。")

    # 加载 Google Embedding 模型
    print("[后端] 正在加载 Google Embedding 模型...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
    print("[后端] Google Embedding 模型加载完成。")

    # 加载向量数据库
    print("[后端] 正在加载向量数据库...")
    db = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    print("[后端] 向量数据库加载完成。")

    # 创建 LLM 实例 (Gemini)
    print("[后端] 正在创建 LLM 实例 (Gemini)...")
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash", 
        google_api_key=google_api_key,
        temperature=0.1,
        convert_system_message_to_human=True
    )
    print("[后端] LLM 实例创建完成。")

    # 创建一个检索器 (不使用重排器)
    print("[后端] 正在创建检索器...")
    retriever = db.as_retriever(search_kwargs={"k": 3}) # 检索最相关的3个文本块
    print("[后端] 检索器创建完成。")

    # 创建提示词模板
    print("[后端] 正在创建提示词模板...")
    template = """
    使用以下提供的上下文来回答最后的问题。
    如果你不知道答案，就说你不知道，不要试图编造答案。
    尽量让答案简洁明了。
    
    上下文: {context}
    
    问题: {question}
    
    有用的回答:
    """
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
    print("[后端] 提示词模板创建完成。")

    # 创建 QA 链
    print("[后端] 正在创建 QA 链...")
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )
    print("[后端] QA 链创建完成。")
    print("[后端] 资源加载完成，应用已准备就绪！")

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """接收问题并返回答案"""
    if not qa_chain:
        raise HTTPException(status_code=503, detail="服务尚未完全初始化，请稍后再试。")
    
    print(f"[后端] 收到问题: {request.question}")
    try:
        # --- 添加调试信息 ---
        print("[后端] 尝试从向量数据库检索相关文档...")
        # 模拟检索过程，实际由 qa_chain.invoke 内部处理
        # 这里只是为了打印，实际检索逻辑在 qa_chain 内部
        retrieved_docs = qa_chain.retriever.get_relevant_documents(request.question)
        print(f"[后端] 检索到 {len(retrieved_docs)} 篇相关文档。")
        for i, doc in enumerate(retrieved_docs):
            print(f"[后端]   文档 {i+1} (来源: {doc.metadata.get('source', '未知')}, 页码: {doc.metadata.get('page', '未知')}):\n[后端]     内容预览: {doc.page_content[:200]}...") # 打印前200字符
        
        # 模拟提示词构建，实际由 qa_chain.invoke 内部处理
        # 这里只是为了打印，实际提示词构建逻辑在 qa_chain 内部
        # prompt_template = QA_CHAIN_PROMPT.format(context="...", question=request.question)
        # print(f"[后端] 构建的提示词 (部分): {prompt_template[:500]}...") # 打印前500字符
        # --- 调试信息结束 ---

        print("[后端] 尝试调用 qa_chain.invoke (这将调用LLM)...")
        result = qa_chain.invoke({"query": request.question})
        print("[后端] qa_chain.invoke 调用成功。")
        print(f"[后端] 生成答案: {result['result']}")
        
        source_documents = []
        for doc in result.get('source_documents', []):
            source_documents.append({
                "source": doc.metadata.get('source', '未知来源'),
                "page": doc.metadata.get('page', '未知页码')
            })

        return {
            "answer": result['result'],
            "source_documents": source_documents
        }
    except Exception as e:
        print(f"[后端] 处理请求时发生错误: {e}")
        import traceback
        traceback.print_exc() # 打印完整的堆栈信息
        raise HTTPException(status_code=500, detail=f"后端处理错误: {e}")

@app.get("/")
def read_root():
    return {"message": "欢迎使用 RAG 问答 API (全API版)。请访问 /docs 查看 API 文档。"}

# 使用 uvicorn 启动 (在命令行中运行: uvicorn main:app --reload)
