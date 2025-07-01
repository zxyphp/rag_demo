
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# 加载环境变量
load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key or google_api_key == 'YOUR_GOOGLE_API_KEY':
    raise ValueError("请在 .env 文件中设置您的 GOOGLE_API_KEY")

# 定义目录
DOCS_DIR = "documents"
PERSIST_DIR = "db"

def main():
    print("开始处理文档...")

    # 检查文档目录
    if not os.path.exists(DOCS_DIR):
        print(f"错误：文档目录 '{DOCS_DIR}' 不存在。")
        return

    documents = []

    # 加载 .doc 文件
    print("正在加载 .docx 文件...")
    loader_docx = DirectoryLoader(
        DOCS_DIR,
        glob="**/*.docx",
        loader_cls=Docx2txtLoader,
        show_progress=True
    )
    documents.extend(loader_docx.load())


    if not documents:
        print(f"在 '{DOCS_DIR}' 目录中没有找到任何 Word 文件 (.doc 或 .docx)。")
        return

    print(f"成功加载 {len(documents)} 个文档页面。")

    # 切分文档
    print("正在切分文档...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    if not texts:
        print("错误：文档切分后为空，请检查您的Word文件内容。")
        return

    print(f"文档已切分为 {len(texts)} 个文本块。")

    # 创建 Embedding 模型
    print("正在初始化 Embedding 模型...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
    print("Embedding 模型初始化完成。")

    # 创建并持久化向量数据库
    print("正在创建向量数据库并存入数据...")
    db = Chroma.from_documents(texts, embeddings, persist_directory=PERSIST_DIR)
    db.persist()
    print("数据处理完成！")
    print(f"向量数据库已成功创建在 '{PERSIST_DIR}' 目录下。")

if __name__ == "__main__":
    main()
