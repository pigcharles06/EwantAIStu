FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製必要文件
COPY requirements.txt .
COPY app.py .
COPY chainlit.md .
COPY chainlit.yaml .
COPY .chainlit .chainlit
COPY public public

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 設置環境變數
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["chainlit", "run", "app.py", "--port", "8000"] 