# FinBuddy - Google Cloud Functions 部署指南

## 檔案說明

- **libs.py**: 完整的交易系統庫，包含所有策略、數據處理、市場模擬功能
- **demo.py**: Google Cloud Functions 入口點，提供 HTTP API 介面
- **requirements.txt**: Python 依賴套件清單

## 本地測試

```bash
# 安裝依賴
pip install -r requirements.txt

# 本地測試
python demo.py
```

## 部署到 Google Cloud Functions

### 1. 安裝 Google Cloud CLI

```bash
# 參考: https://cloud.google.com/sdk/docs/install
```

### 2. 登入並設定專案

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 3. 部署函數

**部署完整版 API（返回 JSON）：**

```bash
gcloud functions deploy get_recommendation \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point get_recommendation \
  --source . \
  --timeout 540s \
  --memory 2GB
```

**部署簡化版 API（返回純文字）：**

```bash
gcloud functions deploy get_recommendation_simple \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point get_recommendation_simple \
  --source . \
  --timeout 540s \
  --memory 2GB
```

### 4. 測試部署的函數

```bash
# 取得函數 URL
gcloud functions describe get_recommendation --format="value(httpsTrigger.url)"

# 測試請求（替換 YOUR_FUNCTION_URL）
curl "https://YOUR_FUNCTION_URL?strategy=max_sharpe&topk=5"
```

## API 使用說明

### 端點 1: `get_recommendation` (完整版)

**請求參數：**
- `strategy`: 策略類型
  - `max_sharpe`: 最大夏普策略（預設）
  - `linear_programming`: 線性規劃策略
- `topk`: 選擇前幾檔股票（預設: 5，僅適用於 max_sharpe）
- `max_weight`: 單檔最大權重（預設: 0.2）
- `date`: 指定日期 YYYY-MM-DD（預設: 最新日期）

**範例請求：**

```bash
# GET 請求
curl "https://YOUR_FUNCTION_URL/get_recommendation?strategy=max_sharpe&topk=3"

# POST 請求
curl -X POST https://YOUR_FUNCTION_URL/get_recommendation \
  -H "Content-Type: application/json" \
  -d '{"strategy": "linear_programming", "max_weight": 0.25}'
```

**回應格式：**

```json
{
  "status": "success",
  "recommendation": "━━━━━━━━━━━━━━━━━━━━━━...",
  "parameters": {
    "strategy": "max_sharpe",
    "topk": 5,
    "max_weight": 0.2,
    "date": "latest"
  }
}
```

### 端點 2: `get_recommendation_simple` (簡化版)

**請求參數：**
- `topk`: 選擇前幾檔股票（預設: 5）

**範例請求：**

```bash
curl "https://YOUR_FUNCTION_URL/get_recommendation_simple?topk=5"
```

**回應格式：** 純文字（適合 Line Bot）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 2024-01-15 每日交易建議
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
策略：MaxSharpeStrategy (topk=5)

💼 推薦持倉配置：
  AAPL      20.0%  (Technology)
  MSFT      20.0%  (Technology)
  ...
```

## Line Bot 整合範例

```python
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
import requests

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')

def send_daily_recommendation(user_id):
    # 呼叫 Google Cloud Function
    response = requests.get(
        'https://YOUR_FUNCTION_URL/get_recommendation_simple?topk=5'
    )
    
    if response.status_code == 200:
        recommendation = response.text
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=recommendation)
        )
```

## 注意事項

1. **首次執行較慢**: 第一次呼叫需要下載所有股票數據（約 3-5 分鐘）
2. **建議使用快取**: 可將 `portfolio_df` 儲存到 Cloud Storage 以加速後續請求
3. **資源配置**: 建議至少配置 2GB 記憶體和 540 秒超時時間
4. **TradingView 憑證**: 請確保 `watchlist_id` 和 `session_id` 有效

## 進階優化

### 使用 Cloud Storage 快取數據

```python
# 在 libs.py 中新增
from google.cloud import storage

def save_to_gcs(df, bucket_name, blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(df.to_csv())

def load_from_gcs(bucket_name, blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return pd.read_csv(blob.download_as_string())
```

### 定時更新數據（Cloud Scheduler）

```bash
# 建立 Cloud Scheduler 任務，每日更新數據
gcloud scheduler jobs create http daily-data-update \
  --schedule="0 9 * * *" \
  --uri="https://YOUR_FUNCTION_URL/update_data" \
  --http-method=POST
```

## 成本估算

- Cloud Functions: 前 200 萬次調用免費
- 記憶體使用: 2GB × 540秒 = 約 $0.003 / 次
- 網路流量: 約 $0.12 / GB

**預估**: 每日 100 次請求 ≈ $10-20 / 月

## 疑難排解

**錯誤: Timeout**
- 增加 `--timeout` 參數到 540s
- 考慮使用數據快取

**錯誤: Memory limit exceeded**
- 增加 `--memory` 參數到 4GB 或 8GB

**錯誤: Module not found**
- 確認 requirements.txt 包含所有依賴
- 檢查 Python 版本是否相容

## 聯絡資訊

如有問題請參考：
- Google Cloud Functions 文檔: https://cloud.google.com/functions
- FinBuddy GitHub: https://github.com/YOUR_REPO
