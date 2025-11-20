from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from scipy.optimize import linprog


class BaseStrategy(ABC):
    """策略基類"""
    
    @abstractmethod
    def calculate_weights(self, market_data: pd.Series, codes: list) -> dict:
        """
        計算投資組合配置權重
        
        Args:
            market_data: 當日市場數據 (包含所有股票的 Close, Sharpe, Beta 等)
            codes: 可交易的股票代碼列表
            
        Returns:
            {ticker: weight} 的字典, weight 總和應為 1.0
        """
        pass


class MaxSharpeStrategy(BaseStrategy):
    """最大夏普策略 - 選擇 Sharpe 最高的前 topk 檔股票"""
    
    def __init__(self, topk: int = 5, max_weight: float = 0.2):
        """
        Args:
            topk: 選擇前幾檔 Sharpe 最高的股票
            max_weight: 單一股票最大權重
        """
        self.topk = topk
        self.max_weight = max_weight
        
    def calculate_weights(self, market_data: pd.Series, codes: list) -> dict:
        """按 Sharpe 排序並分配權重"""
        weights = {code: 0.0 for code in codes}
        
        # 收集有效股票 (Sharpe > 0)
        valid_stocks = []
        for code in codes:
            sharpe_key = f"{code}_Sharpe"
            price_key = f"{code}_Close"
            
            if sharpe_key in market_data.index and price_key in market_data.index:
                sharpe = market_data[sharpe_key]
                price = market_data[price_key]
                
                if pd.notna(sharpe) and pd.notna(price) and sharpe > 0 and price > 0:
                    valid_stocks.append((code, sharpe))
        
        if not valid_stocks:
            weights['CASH'] = 1.0
            return weights
        
        # 按 Sharpe 降序排序, 取前 topk
        valid_stocks.sort(key=lambda x: x[1], reverse=True)
        selected = valid_stocks[:self.topk]
        
        # 平均分配權重
        remaining = 1.0
        for code, _ in selected:
            alloc = min(self.max_weight, remaining)
            weights[code] = alloc
            remaining -= alloc
            if remaining <= 0:
                break
        
        weights['CASH'] = remaining
        return weights


class LinearProgrammingStrategy(BaseStrategy):
    """線性規劃策略 - 在 Beta 約束下最大化 Sharpe"""
    
    def __init__(self, max_weight: float = 0.2, enable_beta_constraint: bool = True):
        """
        Args:
            max_weight: 單一股票最大權重
            enable_beta_constraint: 是否啟用 Beta 約束
        """
        self.max_weight = max_weight
        self.enable_beta_constraint = enable_beta_constraint
        
    def calculate_weights(self, market_data: pd.Series, codes: list) -> dict:
        """用線性規劃求解最佳權重"""
        weights = {code: 0.0 for code in codes}
        
        # 收集有效股票
        valid_codes = []
        sharpe_list = []
        beta_list = []
        
        for code in codes:
            sharpe_key = f"{code}_Sharpe"
            beta_key = f"{code}_Beta"
            price_key = f"{code}_Close"
            
            if all(k in market_data.index for k in [sharpe_key, beta_key, price_key]):
                sharpe = market_data[sharpe_key]
                beta = market_data[beta_key]
                price = market_data[price_key]
                
                if all(pd.notna(v) and np.isfinite(v) for v in [sharpe, beta, price]) and price > 0:
                    valid_codes.append(code)
                    sharpe_list.append(sharpe)
                    beta_list.append(beta)
        
        if not valid_codes:
            weights['CASH'] = 1.0
            return weights
        
        # 設定線性規劃問題
        n = len(valid_codes)
        sharpe = np.array(sharpe_list)
        beta = np.array(beta_list)
        
        # 目標函數: 最大化 Sharpe (轉為最小化 -Sharpe)
        c = -sharpe
        
        # 等式約束: 總權重 = 1
        A_eq = [np.ones(n)]
        b_eq = [1.0]
        
        # 不等式約束: Beta 限制
        A_ub = []
        b_ub = []
        
        if self.enable_beta_constraint and 'betas' in market_data.index:
            beta_threshold = market_data['betas']
            if pd.notna(beta_threshold) and np.isfinite(beta_threshold):
                A_ub.append(beta)
                b_ub.append(beta_threshold)
        
        # 邊界: 0 <= weight <= max_weight
        bounds = [(0, self.max_weight) for _ in range(n)]
        
        # 求解
        res = linprog(
            c, 
            A_ub=A_ub or None, 
            b_ub=b_ub or None,
            A_eq=A_eq, 
            b_eq=b_eq, 
            bounds=bounds, 
            method="highs"
        )
        
        # 處理結果
        if res.success and res.x.sum() > 1e-6:
            for i, code in enumerate(valid_codes):
                weights[code] = res.x[i]
        else:
            weights['CASH'] = 1.0
        
        return weights
