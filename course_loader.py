import os
from typing import List, Dict
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加載環境變量
load_dotenv()

class CourseContentLoader:
    def __init__(self, content_dir: str = "course_content"):
        """初始化課程內容加載器"""
        self.content_dir = content_dir
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # 創建文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
        
        # 設置支援的文件類型
        self.loader_mapping = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": TextLoader,
        }

    def load_document(self, file_path: str) -> List[Document]:
        """加載單個文檔"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in self.loader_mapping:
                loader = self.loader_mapping[file_extension](file_path)
                documents = loader.load()
                logger.info(f"成功加載文件: {file_path}")
                return documents
            else:
                # 使用通用加載器處理其他類型文件
                loader = UnstructuredFileLoader(file_path)
                documents = loader.load()
                logger.info(f"使用通用加載器加載文件: {file_path}")
                return documents
        except Exception as e:
            logger.error(f"加載文件 {file_path} 時發生錯誤: {str(e)}")
            return []

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """處理文檔，包括文本分割"""
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"文檔處理完成，共產生 {len(split_docs)} 個文本片段")
            return split_docs
        except Exception as e:
            logger.error(f"處理文檔時發生錯誤: {str(e)}")
            return []

    def load_all_documents(self) -> List[Document]:
        """加載所有課程文檔"""
        all_documents = []
        
        # 確保目錄存在
        if not os.path.exists(self.content_dir):
            os.makedirs(self.content_dir)
            logger.info(f"創建目錄: {self.content_dir}")
            return all_documents

        # 遍歷目錄中的所有文件
        for root, _, files in os.walk(self.content_dir):
            for file in files:
                file_path = os.path.join(root, file)
                documents = self.load_document(file_path)
                if documents:
                    all_documents.extend(documents)

        logger.info(f"總共加載了 {len(all_documents)} 個文檔")
        return all_documents

    def embed_documents(self) -> bool:
        """將文檔 embedding 到 ChromaDB"""
        try:
            # 加載所有文檔
            documents = self.load_all_documents()
            if not documents:
                logger.warning("沒有找到可用的文檔")
                return False

            # 處理文檔
            processed_documents = self.process_documents(documents)
            if not processed_documents:
                logger.warning("文檔處理後沒有可用內容")
                return False

            # 創建向量存儲
            vectordb = Chroma.from_documents(
                documents=processed_documents,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            
            # 持久化存儲
            vectordb.persist()
            logger.info("文檔已成功 embedding 到 ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Embedding 過程中發生錯誤: {str(e)}")
            return False

def main():
    """主函數"""
    loader = CourseContentLoader()
    success = loader.embed_documents()
    if success:
        print("課程內容已成功加載到向量數據庫")
    else:
        print("加載過程中發生錯誤，請查看日誌了解詳情")

if __name__ == "__main__":
    main() 