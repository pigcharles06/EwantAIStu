import os
import json
import hashlib
from typing import Optional, Dict
import chromadb
from chromadb.config import Settings
from datetime import datetime

class UserManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./user_db")
        
        # 確保用戶集合存在
        try:
            self.collection = self.client.get_collection("users")
        except ValueError:
            self.collection = self.client.create_collection("users")

    def _hash_password(self, password: str) -> str:
        """對密碼進行雜湊處理"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str, email: str) -> bool:
        """註冊新用戶"""
        try:
            # 檢查用戶名是否已存在
            results = self.collection.get(
                where={"username": username}
            )
            if results and results['documents']:
                return False  # 用戶名已存在
            
            # 檢查郵箱是否已存在
            results = self.collection.get(
                where={"email": email}
            )
            if results and results['documents']:
                return False  # 郵箱已存在

            # 創建新用戶
            user_data = {
                "username": username,
                "password": self._hash_password(password),
                "email": email,
                "role": "user",
                "created_at": datetime.now().isoformat(),
                "learning_style": None,
                "interaction_count": 0
            }

            # 將用戶數據存儲到 ChromaDB
            self.collection.add(
                documents=[json.dumps(user_data)],
                metadatas=[{"username": username, "email": email}],
                ids=[username]
            )
            return True
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """驗證用戶"""
        try:
            results = self.collection.get(
                where={"username": username}
            )
            if results and results['documents']:
                user_data = json.loads(results['documents'][0])
                if user_data["password"] == self._hash_password(password):
                    return user_data
        except Exception as e:
            print(f"Authentication error: {str(e)}")
        return None

    def get_user(self, username: str) -> Optional[Dict]:
        """獲取用戶資料"""
        try:
            results = self.collection.get(
                where={"username": username}
            )
            if results and results['documents']:
                return json.loads(results['documents'][0])
        except:
            pass
        return None

    def update_user(self, username: str, update_data: Dict) -> bool:
        """更新用戶資料"""
        try:
            user_data = self.get_user(username)
            if user_data:
                user_data.update(update_data)
                self.collection.update(
                    documents=[json.dumps(user_data)],
                    metadatas=[{"username": username}],
                    ids=[username]
                )
                return True
        except:
            pass
        return False 