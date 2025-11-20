from utils.trader import Trader, MaxSharpeStrategy, LinearProgrammingStrategy
from utils.market import SimulatedMarket

# 建立市場模擬器
simulator = SimulatedMarket(
    watchlist_id="118349730",
    session_id="b379eetq1pojcel6olyymmpo1rd41nng"
)

# 建立數據 (只需執行一次)
simulator.build_portfolio_data(sharpe_window=252, slope_window=365, ma_period=30)

# 方式1: 單一策略回測
#trader = Trader(balance=10000, strategy=MaxSharpeStrategy(topk=5), rebalance_frequency='daily')
#simulator.run(trader)

# 方式2: 比較不同 rebalance 頻率
traders = [
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=10), rebalance_frequency='daily'),
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=10), rebalance_frequency='weekly'),
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=10), rebalance_frequency='monthly'),
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=10), rebalance_frequency='quarterly'),
    Trader(balance=10000, strategy=MaxSharpeStrategy(topk=10), rebalance_frequency='yearly')
]
simulator.run(traders)

# 輸出結果
#simulator.summary()
#simulator.plot_equity_curve(save_path="equity_curve.png", min_drawdown_label=0.15)

# 獲取交易建議
recommendation = simulator.get_trading_recommendation(MaxSharpeStrategy(topk=10))
print(recommendation)