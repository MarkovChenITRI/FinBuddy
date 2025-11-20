# FinBuddy

**FinBuddy** 是一個股市投資組合最佳化與回測系統,結合彩虹圖技術分析、產業動能偵測與數學最佳化,幫助你制定量化交易策略。

## 🚀 快速開始

### 環境需求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (推薦的 Python 套件管理工具)

### 安裝步驟

1. **安裝 uv** (如果尚未安裝)

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **克隆專案**

```bash
git clone https://github.com/MarkovChenITRI/FinBuddy.git
cd FinBuddy
```

3. **建立虛擬環境並安裝依賴**

```bash
# uv 會自動建立虛擬環境並安裝所有依賴
uv sync
```

4. **執行回測**

```bash
# 啟動虛擬環境並執行 main.py
uv run python main.py
```

## 📊 功能特色

### 1. **多策略支援**
- **MaxSharpeStrategy**: 選擇 Sharpe 比率最高的前 N 檔股票
- **LinearProgrammingStrategy**: 在 Beta 約束下最大化投資組合 Sharpe

### 2. **多頻率 Rebalance**
支援三種調倉頻率:
- `daily`: 每日調倉
- `weekly`: 每週調倉 (週一)
- `monthly`: 每月調倉

### 3. **完整的技術指標**
- 彩虹圖波段分析
- 夏普比率計算
- 波動率與 Beta 值
- 產業動能偵測 (黃金/死亡交叉)
- 下跌機率預測

### 4. **視覺化回測報告**
- 權益曲線 (含最大回撤陰影)
- 多策略對比 (含 IQR 區間)
- 年化報酬率、最大回撤、夏普比率等統計指標

## 📖 使用範例

### 基本用法

```python
from utils.trader import Trader, MaxSharpeStrategy
from utils.market import SimulatedMarket

# 建立市場模擬器
simulator = SimulatedMarket()

# 建立數據 (可自訂參數)
simulator.build_portfolio_data(
    sharpe_window=365,  # Sharpe 計算視窗
    slope_window=365,   # 斜率計算視窗
    ma_period=30        # 產業 MA 週期
)

# 建立交易員
trader = Trader(
    balance=10000, 
    strategy=MaxSharpeStrategy(topk=5),
    rebalance_frequency='daily'
)

# 執行回測
simulator.run(trader)

# 查看結果
simulator.summary()
simulator.plot_equity_curve(save_path="equity_curve.png")
```

### 比較不同 Rebalance 頻率

```python
# 建立三個不同頻率的交易員
traders = [
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=5), rebalance_frequency='daily'),
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=5), rebalance_frequency='weekly'),
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=5), rebalance_frequency='monthly'),
]

# 一次執行所有回測
simulator.run(traders)

# 產生對比報告
simulator.summary()
simulator.plot_equity_curve(save_path="comparison.png")
```

## 🔧 進階設定

### TradingView 投資組合

預設使用 TradingView 的 watchlist,若需自訂:

```python
from utils.market import MarketDataProvider

data_provider = MarketDataProvider(
    watchlist_id="YOUR_WATCHLIST_ID",
    session_id="YOUR_SESSION_ID"
)

simulator = SimulatedMarket(data_provider=data_provider)
```

### 策略參數調整

```python
# MaxSharpe 策略
strategy = MaxSharpeStrategy(
    topk=5,          # 選擇前 5 檔股票
    max_weight=0.2   # 單檔最大權重 20%
)

# 線性規劃策略
strategy = LinearProgrammingStrategy(
    max_weight=0.2,              # 單檔最大權重
    enable_beta_constraint=True  # 啟用 Beta 約束
)
```

## 📁 專案結構

```
FinBuddy/
├── main.py                      # 主程式入口
├── utils/
│   ├── trader/
│   │   ├── action.py            # 交易動作定義
│   │   ├── strategies.py        # 交易策略
│   │   └── engine.py            # 交易員引擎
│   └── market/
│       ├── data.py              # 數據提供者
│       └── engine.py            # 市場模擬器
├── notebook/
│   └── 股市計算機v3.ipynb       # 原始研究 notebook
├── pyproject.toml               # 專案配置
└── README.md                    # 本文件
```

## 📈 輸出範例

執行後會產生:

1. **文字報告**
```
📊 Backtest Summary
======================================================================

MaxSharpeStrategy_daily
  💰 Final Value: $15,234.56
  📈 Total Return: 52.35%
  📊 Annual Return: 18.42%
  📉 Max Drawdown: 12.34%
  📐 Sharpe Ratio: 1.85
```

2. **權益曲線圖** (`equity_curve.png`)
   - 單策略: 顯示 drawdown 陰影
   - 多策略: 顯示 IQR 區間與各策略曲線

## 🛠️ 技術細節

- **回測數據**: 過去 15 年股價數據 (via yfinance)
- **指標計算**:
  - Sharpe ratio: 365天滾動視窗
  - 波動率: 年化因子 √252
  - 產業動能: 30/120天雙均線
- **最佳化方法**: scipy.linprog (highs 演算法)

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request!

## 📄 授權

MIT License

---

## 🔗 相關專案

- [FinBuddy-MCP-Server](https://github.com/MarkovChenITRI/FinBuddy-MCP-Server) - MCP Server 整合
- [searxng-docker](https://github.com/searxng/searxng-docker) - 搜尋引擎服務
