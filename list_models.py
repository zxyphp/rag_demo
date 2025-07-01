import os
from dotenv import load_dotenv
import google.generativeai as genai

# 加载环境变量
load_dotenv()

 # 获取您的 Google API Key
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key or google_api_key == 'YOUR_GOOGLE_API_KEY':
    print("错误：请在 .env 文件中设置您的 GOOGLE_API_KEY")
else:
    genai.configure(api_key=google_api_key)
    print("以下是您的 API Key 可用的模型列表：")
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name} (支持生成内容)")
        else:
            print(f"- {m.name} (不支持生成内容)")