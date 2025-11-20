# Google Cloud Functions 部署配置

## 📁 部署檔案

確保這三個檔案在同一個目錄：

```
deploy/
├── main.py       (從 demo.py 重命名，或使用 main.py.gcp)
├── libs.py       (完整庫文件)
└── requirements.txt
```

## 🚀 部署步驟

### 1. 準備部署目錄

```powershell
# 建立部署目錄
mkdir deploy
cd deploy

# 複製檔案
copy ..\libs.py .
copy ..\demo.py main.py
copy ..\requirements.txt .
```

或者使用 main.py.gcp：

```powershell
mkdir deploy
cd deploy
copy ..\libs.py .
copy ..\main.py.gcp main.py
copy ..\requirements.txt .
```

### 2. 確認 requirements.txt

```txt
numpy
pandas
yfinance
scipy
scikit-learn
requests
functions-framework
line-bot-sdk
```

### 3. 部署到 Google Cloud Functions

```bash
gcloud functions deploy hello_http \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point hello_http \
  --source . \
  --timeout 540s \
  --memory 4GB \
  --region asia-east1
```

**重要參數說明：**
- `--runtime python312`: 使用 Python 3.12
- `--entry-point hello_http`: 入口函數名稱
- `--source .`: 當前目錄（包含 main.py, libs.py, requirements.txt）
- `--timeout 540s`: 最大 9 分鐘超時
- `--memory 4GB`: 4GB 記憶體（建議值，因為需要處理大量數據）
- `--region asia-east1`: 亞洲東部區域

### 4. 檢查部署狀態

```bash
# 查看函數資訊
gcloud functions describe hello_http --region asia-east1

# 查看日誌
gcloud functions logs read hello_http --region asia-east1 --limit 50
```

### 5. 測試部署

```bash
# 取得 URL
FUNCTION_URL=$(gcloud functions describe hello_http --region asia-east1 --format="value(httpsTrigger.url)")

# 測試呼叫
curl "$FUNCTION_URL"
curl "$FUNCTION_URL?topk=5"
```

## ⚠️ 常見問題

### 問題 1: ModuleNotFoundError: No module named 'scipy'

**原因**: requirements.txt 未正確部署

**解決方案**:
1. 確認 requirements.txt 在部署目錄
2. 確認 `--source .` 指向正確的目錄
3. 檢查 requirements.txt 內容是否完整

```bash
# 檢查部署目錄
ls -la
# 應該看到: main.py, libs.py, requirements.txt

# 重新部署
gcloud functions deploy hello_http \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point hello_http \
  --source . \
  --timeout 540s \
  --memory 4GB \
  --region asia-east1
```

### 問題 2: Function execution took too long

**原因**: 首次執行需下載數據，超過 60 秒預設超時

**解決方案**: 增加 timeout 到 540 秒（9 分鐘）

```bash
gcloud functions deploy hello_http \
  --timeout 540s \
  --memory 4GB
```

### 問題 3: Memory limit exceeded

**原因**: 預設 256MB 記憶體不足

**解決方案**: 增加到 4GB 或 8GB

```bash
gcloud functions deploy hello_http \
  --memory 4GB
```

或更大：

```bash
gcloud functions deploy hello_http \
  --memory 8GB
```

### 問題 4: Line 訊息發送失敗

**檢查事項**:
1. LINE_CHANNEL_ACCESS_TOKEN 是否正確
2. LINE_USER_ID 是否正確
3. Line Bot API 是否啟用

**查看錯誤日誌**:
```bash
gcloud functions logs read hello_http --region asia-east1 --limit 50
```

## 📊 監控

### 查看即時日誌

```bash
gcloud functions logs read hello_http \
  --region asia-east1 \
  --limit 100 \
  --format "table(timestamp,textPayload)"
```

### 查看錯誤

```bash
gcloud functions logs read hello_http \
  --region asia-east1 \
  --severity ERROR
```

## 🔧 更新部署

修改程式碼後重新部署：

```bash
# 在 deploy 目錄中
gcloud functions deploy hello_http \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point hello_http \
  --source . \
  --timeout 540s \
  --memory 4GB \
  --region asia-east1
```

## 💰 成本控制

```bash
# 設定最大實例數
gcloud functions deploy hello_http \
  --max-instances 5

# 設定最小實例數（保持熱啟動，但增加成本）
gcloud functions deploy hello_http \
  --min-instances 0  # 預設值，節省成本

# 設定併發請求數
gcloud functions deploy hello_http \
  --concurrency 1  # 每個實例同時處理 1 個請求
```

## 🗑️ 刪除函數

```bash
gcloud functions delete hello_http --region asia-east1
```

## 📝 完整部署命令（推薦）

```bash
gcloud functions deploy hello_http \
  --gen2 \
  --runtime python312 \
  --region asia-east1 \
  --source . \
  --entry-point hello_http \
  --trigger-http \
  --allow-unauthenticated \
  --timeout 540s \
  --memory 4GB \
  --max-instances 5 \
  --min-instances 0 \
  --concurrency 1
```
