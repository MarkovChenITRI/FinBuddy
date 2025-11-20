from dataclasses import dataclass
from typing import Dict
import pandas as pd


@dataclass
class PortfolioSnapshot:
    """投資組合快照 - 記錄每日狀態"""
    timestamp: pd.Timestamp
    cash: float
    positions: Dict[str, int]  # {ticker: units}
    total_value: float
