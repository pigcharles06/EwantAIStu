# AI助教與虛擬學生系統

這是一個基於 Chainlit 和 OpenAI 開發的智能教育輔助系統，提供 AI 助教和虛擬學生功能。

## 功能特點

- AI助教功能
  - 回答課程相關問題
  - 提供知識點總結
  - 課程講義整理

- 虛擬學生功能
  - 模擬學習討論場景
  - 互動式學習體驗

- 用戶系統
  - 使用者登入與註冊
  - 個人學習進度追蹤
  - 互動記錄保存

## 技術架構

- 前端界面：Chainlit
- 向量數據庫：ChromaDB
- LLM模型：OpenAI
- Embedding：OpenAI

## 安裝說明

1. 安裝依賴：
```bash
pip install -r requirements.txt
```

2. 配置環境變量：
- 複製 `.env.example` 為 `.env`
- 填入您的 OpenAI API 密鑰

3. 運行應用：
```bash
chainlit run app.py
```

## 使用說明

1. 訪問 http://localhost:8000
2. 登入系統
3. 選擇想要使用的功能（AI助教/虛擬學生）
4. 開始互動學習

## 注意事項

- 請確保您有有效的 OpenAI API 密鑰
- 確保網絡連接穩定
- 建議使用最新版本的瀏覽器 