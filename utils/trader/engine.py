import pandas as pd
from typing import Dict
from .strategies import BaseStrategy
from .action import PortfolioSnapshot


class Trader:
    """交易員 - 管理資金、持倉與策略執行"""
    
    def __init__(self, balance: float, strategy: BaseStrategy, rebalance_frequency: str = 'daily'):
        """
        Args:
            balance: 初始資金
            strategy: 交易策略 (BaseStrategy 的子類)
            rebalance_frequency: rebalance 頻率 ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
        """
        self.initial_balance = balance
        self.cash = balance
        self.inventory = {}  # {ticker: units}
        self.strategy = strategy
        self.rebalance_frequency = rebalance_frequency.lower()
        
        self.portfolio_history = []  # List[PortfolioSnapshot]
        self.last_rebalance_date = None
        
    def _should_rebalance(self, current_date: pd.Timestamp) -> bool:
        """判斷是否該執行 rebalance"""
        if self.last_rebalance_date is None:
            return True
            
        if self.rebalance_frequency == 'daily':
            return True
        elif self.rebalance_frequency == 'weekly':
            # 每週一 rebalance
            return current_date.weekday() == 0 and \
                   (current_date - self.last_rebalance_date).days >= 7
        elif self.rebalance_frequency == 'monthly':
            # 每月第一個交易日 rebalance
            return current_date.month != self.last_rebalance_date.month
        elif self.rebalance_frequency == 'quarterly':
            # 每季第一個交易日 rebalance (1, 4, 7, 10月)
            quarter_months = [1, 4, 7, 10]
            return current_date.month in quarter_months and \
                   current_date.month != self.last_rebalance_date.month
        elif self.rebalance_frequency == 'yearly':
            # 每年第一個交易日 rebalance (1月)
            return current_date.year != self.last_rebalance_date.year
        
        return False
        
    def decide(self, market_data: pd.Series, codes: list) -> Dict[str, float]:
        """
        根據策略決定配置權重
        
        Args:
            market_data: 當日市場數據
            codes: 可交易股票列表
            
        Returns:
            {ticker: weight} 字典
        """
        return self.strategy.calculate_weights(market_data, codes)
        
    def execute_trades(self, weights: Dict[str, float], market_data: pd.Series):
        """
        執行交易 - 根據權重調整持倉
        
        Args:
            weights: 目標配置權重
            market_data: 當日市場數據 (用於取得價格)
        """
        current_value = self.get_portfolio_value(market_data)
        
        # 計算目標持倉
        new_inventory = {}
        for ticker, weight in weights.items():
            if ticker == 'CASH':
                continue
                
            price_key = f'{ticker}_Close'
            if price_key not in market_data.index:
                continue
                
            price = market_data[price_key]
            if pd.isna(price) or price <= 0:
                continue
                
            if weight > 0:
                target_value = current_value * weight
                units = int(target_value / price)
                if units > 0:
                    new_inventory[ticker] = units
        
        # 計算實際使用金額
        used = sum(
            units * market_data[f'{ticker}_Close']
            for ticker, units in new_inventory.items()
            if f'{ticker}_Close' in market_data.index
        )
        
        # 更新持倉與現金
        self.cash = current_value - used
        self.inventory = new_inventory
        self.last_rebalance_date = market_data.name
        
    def update_daily_snapshot(self, market_data: pd.Series):
        """記錄每日投資組合狀態"""
        snapshot = PortfolioSnapshot(
            timestamp=market_data.name,
            cash=self.cash,
            positions=self.inventory.copy(),
            total_value=self.get_portfolio_value(market_data)
        )
        self.portfolio_history.append(snapshot)
        
    def get_portfolio_value(self, market_data: pd.Series) -> float:
        """計算當前投資組合總價值"""
        total = self.cash
        for ticker, units in self.inventory.items():
            price_key = f'{ticker}_Close'
            if price_key in market_data.index:
                price = market_data[price_key]
                if pd.notna(price) and price > 0:
                    total += units * price
        return total
        
    def get_positions(self) -> Dict[str, int]:
        """取得當前持倉"""
        return self.inventory.copy()
