# FinBuddy - Google Cloud Functions + Line Bot 部署指南

## 📦 檔案說明

- **libs.py**: 完整的交易系統庫（策略、數據處理、市場模擬）
- **demo.py**: Google Cloud Functions 入口點，包含 Line Bot 整合
- **test_line_bot.py**: 本地測試腳本
- **requirements.txt**: Python 依賴套件

## 🔑 設定 Line Bot

### 1. 取得 Line Bot 憑證

1. 前往 [Line Developers Console](https://developers.line.biz/)
2. 建立 Messaging API Channel
3. 取得以下資訊：
   - **Channel Access Token**: 長期的存取令牌
   - **User ID**: 你的 Line 使用者 ID

### 2. 修改 demo.py 中的憑證

```python
LINE_CHANNEL_ACCESS_TOKEN = '你的_Channel_Access_Token'
LINE_USER_ID = '你的_User_ID'
```

## 🧪 本地測試

### 安裝依賴

```powershell
pip install -r requirements.txt
```

### 測試 Line Bot 功能

```powershell
python test_line_bot.py
```

這會：
1. ✅ 初始化市場模擬器
2. 📊 建立投資組合數據
3. 💡 生成今日交易建議
4. 📤 發送訊息到你的 Line

## 🚀 部署到 Google Cloud Functions

### 1. 部署主要函數（推送到 Line）

```bash
gcloud functions deploy hello_http \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point hello_http \
  --timeout 540s \
  --memory 2GB \
  --set-env-vars LINE_CHANNEL_ACCESS_TOKEN="你的token",LINE_USER_ID="你的user_id"
```

**更安全的做法（使用 Secret Manager）：**

```bash
# 建立 Secret
echo -n "你的token" | gcloud secrets create line-channel-token --data-file=-
echo -n "你的user_id" | gcloud secrets create line-user-id --data-file=-

# 部署時引用 Secret
gcloud functions deploy hello_http \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point hello_http \
  --timeout 540s \
  --memory 2GB \
  --set-secrets 'LINE_CHANNEL_ACCESS_TOKEN=line-channel-token:latest,LINE_USER_ID=line-user-id:latest'
```

### 2. 取得函數 URL

```bash
gcloud functions describe hello_http --format="value(httpsTrigger.url)"
```

### 3. 測試部署的函數

```bash
# 基本測試（topk=10）
curl "https://YOUR_FUNCTION_URL"

# 指定參數
curl "https://YOUR_FUNCTION_URL?topk=5&strategy=max_sharpe"

# 不發送 Line 訊息（僅返回結果）
curl "https://YOUR_FUNCTION_URL?topk=10&send_line=false"
```

## 📱 API 使用說明

### 主要端點: `hello_http`

**功能**: 生成交易建議並自動推送到 Line Bot

**請求參數**:
- `topk`: 選擇前幾檔股票（預設: 10）
- `strategy`: 策略類型（預設: max_sharpe）
  - `max_sharpe`: 最大夏普策略
  - `linear_programming`: 線性規劃策略
- `send_line`: 是否發送 Line 訊息（預設: true）

**範例請求**:

```bash
# 使用預設參數（topk=10）並推送到 Line
curl "https://YOUR_FUNCTION_URL"

# 選擇 top 5 股票
curl "https://YOUR_FUNCTION_URL?topk=5"

# 使用線性規劃策略
curl "https://YOUR_FUNCTION_URL?strategy=linear_programming"

# 只取得建議但不發送 Line
curl "https://YOUR_FUNCTION_URL?send_line=false"
```

**成功回應**:

```json
{
  "status": "success",
  "message": "Trading recommendation sent to Line",
  "recommendation": "━━━━━━━━━━━━━━━━━━━━━━...\n📅 2024-01-15 每日交易建議\n..."
}
```

**Line 訊息格式**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 2024-01-15 每日交易建議
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
策略：MaxSharpeStrategy (topk=10)

💼 推薦持倉配置：
  AAPL      20.0%  (Technology)
  MSFT      20.0%  (Technology)
  GOOGL     20.0%  (Technology)
  ...

📊 市場概況：
  整體趨勢：0.75 (偏多)
  大盤位置：接近高點
  市場波動：0.18 (中等)

💡 操作建議：
  • 優先配置：Technology, Healthcare 產業
  • 減持調整：Energy 產業
  • 現金比例：保留 0.0% 應對波動
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## ⏰ 定時推送設定（Cloud Scheduler）

### 1. 建立每日定時任務

```bash
# 每個交易日早上 9:00 自動推送
gcloud scheduler jobs create http daily-trading-recommendation \
  --schedule="0 9 * * 1-5" \
  --time-zone="Asia/Taipei" \
  --uri="https://YOUR_FUNCTION_URL?topk=10" \
  --http-method=GET
```

### 2. 建立多個排程（不同策略）

```bash
# 早上 9:00 - MaxSharpe Top 10
gcloud scheduler jobs create http morning-maxsharpe \
  --schedule="0 9 * * 1-5" \
  --time-zone="Asia/Taipei" \
  --uri="https://YOUR_FUNCTION_URL?topk=10&strategy=max_sharpe" \
  --http-method=GET

# 下午 3:00 - LinearProgramming
gcloud scheduler jobs create http afternoon-lp \
  --schedule="0 15 * * 1-5" \
  --time-zone="Asia/Taipei" \
  --uri="https://YOUR_FUNCTION_URL?strategy=linear_programming" \
  --http-method=GET
```

### 3. 測試排程

```bash
gcloud scheduler jobs run daily-trading-recommendation
```

## 🛡️ 安全性最佳實踐

### 1. 不要在程式碼中直接寫入 Token

❌ **不好的做法**:
```python
LINE_CHANNEL_ACCESS_TOKEN = 'Es+feMvp7Uwg+nI...'  # 硬編碼
```

✅ **好的做法**:
```python
import os
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
```

### 2. 使用環境變數或 Secret Manager

```python
# demo.py 修改為
import os

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    'LINE_CHANNEL_ACCESS_TOKEN',
    'Es+feMvp7Uwg+nIcgB66iAKWVD1dOKRcXzYwPmSbko+b0Vf21iko3s7dRwEFX1tfToR8mrW78XUACEd/uyecCF/Uqd9LgvkchpPEPiODdX4L8BU4b6pXHzFvlDoAfsP9xIFSMG+rmVzQURS+7uBnegdB04t89/1O/w1cDnyilFU='
)
LINE_USER_ID = os.environ.get(
    'LINE_USER_ID',
    'Udba3ff0abbe6607af5a5cfc2e2ddc8a1'
)
```

### 3. 加入驗證機制

```python
@functions_framework.http
def hello_http(request):
    # 驗證 API Key
    api_key = request.headers.get('X-API-Key')
    if api_key != os.environ.get('API_KEY'):
        return {'error': 'Unauthorized'}, 401
    
    # ... 原有邏輯
```

## 📊 監控與日誌

### 查看 Cloud Functions 日誌

```bash
gcloud functions logs read hello_http --limit 50
```

### 查看 Line Bot 發送狀態

在程式中已包含錯誤處理：
```python
def send_line_message(text):
    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        return True
    except Exception as e:
        print(f"❌ Line 訊息發送失敗: {e}")
        return False
```

## 💰 成本估算

### Google Cloud Functions
- 前 200 萬次調用: 免費
- 記憶體 2GB × 540秒: ~$0.003/次
- 網路流量: ~$0.12/GB

### Line Messaging API
- 推送訊息: 免費（每月 500 則）
- 超過額度: ~$0.10/則

**預估月成本**（每日 1 次推送）:
- Cloud Functions: ~$3-5
- Line API: 免費（30 則/月 < 500）
- **總計**: **$3-5/月**

## 🔧 疑難排解

### Line 訊息發送失敗

**錯誤**: `401 Unauthorized`
- ✅ 檢查 `LINE_CHANNEL_ACCESS_TOKEN` 是否正確
- ✅ 確認 Token 未過期

**錯誤**: `400 Bad Request`
- ✅ 檢查 `LINE_USER_ID` 格式是否正確（應為 `U` 開頭）

**錯誤**: `429 Too Many Requests`
- ✅ Line 免費版每月限 500 則推送
- ✅ 考慮升級 Line 方案或減少推送頻率

### Cloud Function Timeout

**錯誤**: `Function execution took 540001 ms, finished with status: 'timeout'`

**解決方案**:
```bash
# 增加 timeout 到最大值（9 分鐘）
gcloud functions deploy hello_http \
  --timeout 540s \
  --memory 4GB
```

### 記憶體不足

**錯誤**: `Memory limit exceeded`

**解決方案**:
```bash
# 增加記憶體到 4GB 或 8GB
gcloud functions deploy hello_http \
  --memory 4GB
```

## 📞 支援

- Line Developers 文檔: https://developers.line.biz/
- Google Cloud Functions 文檔: https://cloud.google.com/functions
- Line Bot SDK: https://github.com/line/line-bot-sdk-python

## 🎯 快速檢查清單

部署前確認：
- [ ] Line Bot Token 和 User ID 已正確設定
- [ ] requirements.txt 包含 `line-bot-sdk`
- [ ] 本地測試通過 (`python test_line_bot.py`)
- [ ] Cloud Function 部署成功
- [ ] 手動觸發測試成功
- [ ] Cloud Scheduler 設定完成（可選）
- [ ] 監控和告警設定完成（可選）
