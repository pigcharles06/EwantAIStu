# 使用Python 3.11基礎鏡像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製必要文件
COPY ./requirements.txt /app/requirements.txt
COPY ./app.py /app/app.py
COPY ./course_loader.py /app/course_loader.py
COPY ./user_manager.py /app/user_manager.py
COPY ./.chainlit /app/.chainlit
COPY ./public /app/public

# 安裝Python依賴
RUN pip3 install -r requirements.txt

# 設置環境變量
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
