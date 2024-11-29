import os
import chainlit as cl
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_community.vectorstores import Chroma
import chromadb
from chromadb.config import Settings
import logging
from course_loader import CourseContentLoader
from user_manager import UserManager
import json
from datetime import datetime
from typing import Optional

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加載環境變量
load_dotenv()

# 初始化用戶管理器
user_manager = UserManager()

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """處理用戶認證和註冊"""
    try:
        # 檢查當前路徑是否為註冊頁面
        is_register = "/auth/register" in cl.context.current_request.url.path
        
        if is_register:
            # 檢查用戶是否已存在
            existing_user = user_manager.get_user(username)
            if existing_user:
                logger.warning(f"用戶已存在: {username}")
                return None
            
            # 創建新用戶
            success = user_manager.register_user(
                username=username,
                password=password,
                email=username
            )
            
            if success:
                logger.info(f"註冊成功: {username}")
                return cl.User(
                    identifier=username,
                    metadata={
                        "role": "user",
                        "email": username,
                        "provider": "credentials"
                    }
                )
            else:
                logger.error(f"註冊失敗: {username}")
                return None
        else:
            # 登入流程
            user_data = user_manager.authenticate_user(username, password)
            if user_data:
                logger.info(f"登入成功: {username}")
                return cl.User(
                    identifier=username,
                    metadata={
                        "role": user_data["role"],
                        "email": user_data["email"],
                        "provider": "credentials"
                    }
                )
            else:
                logger.warning(f"登入失敗: {username}")
                return None
    
    except Exception as e:
        logger.error(f"認證錯誤: {str(e)}")
        return None

@cl.on_chat_start
async def start():
    # 獲取當前用戶
    user = cl.user_session.get("user")
    await cl.Message(f"歡迎使用，{user.identifier}！").send()

    # 檢查是否需要重新加載課程內容
    if not os.path.exists("./chroma_db") or not os.listdir("./chroma_db"):
        await cl.Message("正在加載課程內容...").send()
        loader = CourseContentLoader()
        success = loader.embed_documents()
        if success:
            await cl.Message("課程內容加載完成！").send()
        else:
            await cl.Message("課程內容加載失敗，但您仍可以使用基本功能。").send()

    # 初始化用戶設置
    settings = {
        "learning_style": None,
        "difficulty_level": "medium",
        "interaction_count": 0
    }
    cl.user_session.set("settings", settings)
    
    welcome_message = f"""歡迎使用AI助教系統！

您可以：
1. 問我任何課程相關的問題
2. 請我幫您總結知識點
3. 與我討論學習心得
4. 與虛擬學生一起學習和討論

使用指令：
- /teacher - 切換到AI助教模式
- /student - 切換到虛擬學生模式
- /reload - 重新加載課程內容
- /style [visual/logical/practical] - 設置您的學習風格
- /history - 查看學習歷史記錄
- /progress - 查看學習進度報告

當前模式：AI助教"""

    await cl.Message(welcome_message).send()

@cl.on_settings_update
async def setup_agent(settings):
    if settings.get("mode") == "register":
        cl.user_session.set("register_mode", True)
        await cl.Message("請輸入您的電子郵件和密碼來註冊新帳號。").send()
    else:
        cl.user_session.set("register_mode", False)
        await cl.Message("請輸入您的電子郵件和密碼來登入。").send()

# 檢查 API 密鑰
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("請在 .env 文件中設置 OPENAI_API_KEY")

try:
    # 初始化 OpenAI
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 初始化 ChatGPT 模型
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo-1106",
        temperature=0.7,
        max_tokens=2000,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True
    )

    # 初始化 ChromaDB
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )

except Exception as e:
    logger.error(f"初始化錯誤: {str(e)}")
    raise

# AI助教提示模板
TEACHER_TEMPLATE = """你是一位專業的AI助教，名字叫做 Professor AI。
你的職責是：
1. 回答學生的課程相關問題
2. 提供知識點總結
3. 幫助整理課程內容
4. 根據學生程度調整回答深度

當前問題：{question}

相關課程內容：{context}

回答要求：
1. 使用繁體中文
2. 以專業、友善且具體的方式回答
3. 如果問題不清楚，請禮貌地要求學生提供更多信息
4. 適時提供例子或類比來幫助理解
5. 回答後可以提供延伸思考問題
6. 優先使用提供的課程內容進行回答"""

# 虛擬學生提示模板
STUDENT_TEMPLATE = """你是一位積極好學的虛擬學生，名字叫做 Student AI。
你的特點是：
1. 喜歡提出深入的問題
2. 會主動分享自己的想法
3. 樂於與其他同學討論
4. 善於舉例說明

討論主題：{topic}

相關課程內容：{context}

回應要求：
1. 使用繁體中文
2. 以學生的身份回應
3. 表現出求知慾和學習熱情
4. 提出相關的問題或自己的想法
5. 分享自己的學習心得或經驗
6. 可以引用課程內容來支持你的觀點"""

# 創建 LLM 鏈
teacher_chain = LLMChain(
    llm=llm,
    prompt=ChatPromptTemplate.from_template(TEACHER_TEMPLATE)
)

student_chain = LLMChain(
    llm=llm,
    prompt=ChatPromptTemplate.from_template(STUDENT_TEMPLATE)
)

# 存儲當前角色的全局變量
current_role = "AI助教"

@cl.on_message
async def main(message: cl.Message):
    """處理用戶消息"""
    try:
        # 獲取用戶設置
        settings = cl.user_session.get("settings", {})
        user_message = message.content
        
        # 處理特殊指令
        if user_message.lower() == "/teacher":
            global current_role
            current_role = "AI助教"
            await cl.Message("已切換到AI助教模式。我是Professor AI，請問有什麼我可以幫助您的嗎？").send()
            return
        elif user_message.lower() == "/student":
            current_role = "虛擬學生"
            await cl.Message("已切換到虛擬學生模式。我是Student AI，很高興能和您一起學習！").send()
            return
        elif user_message.lower() == "/reload":
            await cl.Message("正在重新加載課程內容...").send()
            loader = CourseContentLoader()
            success = loader.embed_documents()
            if success:
                await cl.Message("課程內容已重新加載完成！").send()
            else:
                await cl.Message("課程內容重新加載失敗。").send()
            return
        elif user_message.lower().startswith("/style"):
            style = user_message.lower().split()[-1]
            if style in ["visual", "logical", "practical"]:
                settings["learning_style"] = style
                cl.user_session.set("settings", settings)
                # 更新用戶資料
                user = cl.user_session.get("user")
                user_manager.update_user(user.identifier, {"learning_style": style})
                await cl.Message(f"已更新您的學習風格為：{style}").send()
            return
        elif user_message.lower() == "/progress":
            user = cl.user_session.get("user")
            user_data = user_manager.get_user(user.identifier)
            progress_info = f"""學習進度報告：
- 學習風格：{user_data.get('learning_style', '未設置')}
- 難度級別：{settings.get('difficulty_level', 'medium')}
- 互動次數：{settings.get('interaction_count', 0)}"""
            await cl.Message(progress_info).send()
            return

        try:
            # 更新互動次數
            settings["interaction_count"] = settings.get("interaction_count", 0) + 1
            cl.user_session.set("settings", settings)

            # 從向量存儲中檢索相關內容
            docs = vectorstore.similarity_search(user_message, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])

            if current_role == "AI助教":
                # 調用AI助教回答
                response = await teacher_chain.ainvoke({
                    "question": user_message,
                    "context": context
                })
                await cl.Message(response["text"]).send()
            else:
                # 調用虛擬學生答
                response = await student_chain.ainvoke({
                    "topic": user_message,
                    "context": context
                })
                await cl.Message(response["text"]).send()

        except Exception as e:
            error_message = f"處理您的請求時發生錯誤：{str(e)}\n請稍後再試或重新提問。"
            await cl.Message(error_message).send()
            logger.error(f"處理消息錯誤: {str(e)}")
        
    except Exception as e:
        logger.error(f"主要處理流程錯誤: {str(e)}")
        await cl.Message("系統發生錯誤，請稍後再試。").send()

if __name__ == "__main__":
    print("Starting the AI Teaching Assistant System...")