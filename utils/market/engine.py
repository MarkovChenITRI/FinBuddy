import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from typing import List, Union
from .data import MarketDataProvider
from ..trader.engine import Trader


class SimulatedMarket:
    """模擬市場環境 - 執行回測與視覺化"""
    
    def __init__(self, data_provider: MarketDataProvider = None, 
                 watchlist_id: str = None, session_id: str = None):
        """
        Args:
            data_provider: 數據提供者 (可選, 若為 None 則使用預設或自訂 ID)
            watchlist_id: TradingView watchlist ID (可選)
            session_id: TradingView session ID (可選)
        """
        if data_provider:
            self.data_provider = data_provider
        elif watchlist_id and session_id:
            self.data_provider = MarketDataProvider(watchlist_id=watchlist_id, session_id=session_id)
        else:
            self.data_provider = MarketDataProvider()
        
        self.portfolio_df = None
        self._traders = {}  # {label: Trader}
        
    def build_portfolio_data(self, sharpe_window: int = 365, slope_window: int = 365, ma_period: int = 30):
        """
        建立投資組合數據
        
        Args:
            sharpe_window: 計算 Sharpe 比率的視窗大小 (預設: 365天)
            slope_window: 計算斜率的視窗大小 (預設: 365天)
            ma_period: 產業移動平均的短期週期 (預設: 30天, 長期為 30*4=120天)
        """
        watchlist = self.data_provider.get_watchlist()
        self.portfolio_df = self.data_provider.build_portfolio_data(
            watchlist, 
            sharpe_window=sharpe_window, 
            slope_window=slope_window, 
            ma_period=ma_period
        )
        print(f"✅ Portfolio data built: {self.portfolio_df.shape[0]} days, {self.portfolio_df.shape[1]} columns")
        
    def run(self, trader_or_traders: Union[Trader, List[Trader]]):
        """
        執行回測
        
        Args:
            trader_or_traders: 單一 Trader 或 Trader 列表
        """
        if self.portfolio_df is None:
            print("⚠️ No portfolio data. Building data first...")
            self.build_portfolio_data()
        
        # 統一轉換成列表
        traders = [trader_or_traders] if isinstance(trader_or_traders, Trader) else trader_or_traders
        
        # 執行回測
        for trader in traders:
            label = f"{trader.strategy.__class__.__name__}_{trader.rebalance_frequency}"
            self._traders[label] = trader
            self._run_single_trader(trader)
            
    def _run_single_trader(self, trader: Trader):
        """執行單一 trader 的回測"""
        watchlist = self.data_provider.get_watchlist()
        codes = watchlist.tolist()
        
        for date in tqdm(self.portfolio_df.index, desc=f"Backtest ({trader.rebalance_frequency})"):
            market_data = self.portfolio_df.loc[date]
            
            # 判斷是否該 rebalance
            if trader._should_rebalance(date):
                weights = trader.decide(market_data, codes)
                trader.execute_trades(weights, market_data)
            
            # 記錄每日狀態
            trader.update_daily_snapshot(market_data)
            
    def summary(self):
        """輸出回測摘要"""
        if not self._traders:
            print("⚠️ No traders to summarize. Run backtest first.")
            return
        
        print("\n" + "="*70)
        print("📊 Backtest Summary")
        print("="*70)
        
        for label, trader in self._traders.items():
            self._print_trader_stats(label, trader)
            print("-"*70)
            
    def _print_trader_stats(self, label: str, trader: Trader):
        """列印單一 trader 的統計資訊"""
        history = [snap.total_value for snap in trader.portfolio_history]
        dates = [snap.timestamp for snap in trader.portfolio_history]
        
        if not history:
            print(f"\n{label}: No history data")
            return
        
        initial = trader.initial_balance
        final = history[-1]
        days = (dates[-1] - dates[0]).days
        annual_return = (final / initial) ** (365 / days) - 1 if days > 0 else 0
        
        # 計算最大回撤
        peak = pd.Series(history).cummax()
        drawdown = (peak - pd.Series(history)) / peak
        max_dd = drawdown.max()
        
        # 計算 Sharpe (簡化版)
        returns = pd.Series(history).pct_change().dropna()
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        print(f"\n{label}")
        print(f"  💰 Final Value: ${final:,.2f}")
        print(f"  📈 Total Return: {(final/initial - 1)*100:.2f}%")
        print(f"  📊 Annual Return: {annual_return*100:.2f}%")
        print(f"  📉 Max Drawdown: {max_dd*100:.2f}%")
        print(f"  📐 Sharpe Ratio: {sharpe:.2f}")
    
    def get_trading_recommendation(self, strategy, date: pd.Timestamp = None) -> str:
        """
        生成每日交易建議
        
        Args:
            strategy: 交易策略實例
            date: 指定日期 (預設為最新日期)
            
        Returns:
            格式化的交易建議文字
        """
        if self.portfolio_df is None:
            return "⚠️ 請先執行 build_portfolio_data() 建立數據"
        
        # 取得日期
        if date is None:
            date = self.portfolio_df.index[-1]
        elif date not in self.portfolio_df.index:
            return f"⚠️ 日期 {date} 不在數據範圍內"
        
        market_data = self.portfolio_df.loc[date]
        watchlist = self.data_provider.get_watchlist()
        codes = watchlist.tolist()
        watchlist_dict = watchlist.todict()
        
        # 取得策略建議權重
        weights = strategy.calculate_weights(market_data, codes)
        
        # 建立股票到產業的映射
        code_to_industry = {}
        for industry, providers in watchlist_dict.items():
            for provider_codes in providers.values():
                for code in provider_codes:
                    code_to_industry[code] = industry
        
        # 建立輸出
        lines = []
        lines.append("━" * 43)
        lines.append(f"📅 {date.strftime('%Y-%m-%d')} 每日交易建議")
        lines.append("━" * 43)
        
        strategy_name = strategy.__class__.__name__
        if hasattr(strategy, 'topk'):
            strategy_name += f" (topk={strategy.topk})"
        lines.append(f"策略：{strategy_name}")
        
        lines.append("\n💼 推薦持倉配置：")
        
        # 排序權重並顯示
        sorted_weights = sorted([(k, v) for k, v in weights.items() if k != 'CASH' and v > 0], 
                               key=lambda x: x[1], reverse=True)
        
        for code, weight in sorted_weights:
            industry = code_to_industry.get(code, "Unknown")
            lines.append(f"  {code:8s}  {weight*100:5.1f}%  ({industry})")
        
        if 'CASH' in weights:
            lines.append(f"  現金      {weights['CASH']*100:5.1f}%")
        
        # 市場概況
        lines.append("\n📊 市場概況：")
        trend = market_data.get('Trend', 0)
        trend_desc = "偏多" if trend > 0.6 else "偏空" if trend < 0.4 else "中性"
        lines.append(f"  整體趨勢：{trend:.2f} ({trend_desc})")
        
        # 大盤位置描述
        segment = int(market_data.get('segments', 5))
        segment_desc = {
            1: "嚴重超跌 (極度弱勢區間)",
            2: "深度超跌 (弱勢區間)",
            3: "超跌整理 (偏弱區間)",
            4: "低檔盤整 (中性偏弱)",
            5: "中性區間 (均衡位置)",
            6: "偏強整理 (中性偏強)",
            7: "接近歷史高點 (強勢區間)",
            8: "突破新高 (偏熱區間)",
            9: "極度高估 (過熱區間)"
        }.get(segment, "未知區間")
        lines.append(f"  大盤位置：{segment_desc}")
        
        volatility = market_data.get('volatilities', 0)
        vol_desc = "低" if volatility < 0.15 else "高" if volatility > 0.25 else "中等"
        lines.append(f"  市場波動：{volatility:.2f} ({vol_desc})")
        
        # 操作建議
        lines.append("\n💡 操作建議：")
        
        # 分類產業
        bullish = []
        bearish = []
        
        for industry in watchlist_dict.keys():
            crossover_state = market_data.get(f'{industry}_Crossover_State', 0)
            if crossover_state == 1:
                bullish.append(industry)
            else:
                bearish.append(industry)
        
        if bullish:
            lines.append(f"  • 優先配置：{', '.join(bullish)} 產業")
        if bearish:
            lines.append(f"  • 減持調整：{', '.join(bearish)} 產業")
        
        cash_ratio = weights.get('CASH', 0)
        lines.append(f"  • 現金比例：保留 {cash_ratio*100:.1f}% 應對波動")
        
        # 建議再平衡頻率
        best_freq = self._get_best_rebalance_frequency(strategy)
        if best_freq:
            lines.append(f"\n📌 建議再平衡頻率：{best_freq['frequency']}")
            dd_count = best_freq['drawdown_count']
            lines.append(f"   歷史年化收益：{best_freq['annual_return']*100:.1f}% - {best_freq['avg_drawdown']*100:.1f}%（{dd_count}次） = {best_freq['score']*100:.1f}%")
        
        lines.append("━" * 43)
        
        return "\n".join(lines)
    
    def _calculate_average_drawdown(self, history, min_drawdown_threshold=0.15):
        """計算超過門檻的平均回撤
        
        Args:
            history: 資產歷史價值列表
            min_drawdown_threshold: 回撤門檻 (預設 0.15，即 15%)
            
        Returns:
            (average_drawdown, count): 超過門檻的平均回撤值和次數
        """
        series = pd.Series(history)
        peak = series.cummax()
        drawdown = (series - peak) / peak
        
        significant_drawdowns = []  # 儲存超過門檻的回撤
        in_drawdown = False
        current_dd = 0
        
        for dd in drawdown:
            if dd < 0:  # 在回撤中
                if not in_drawdown:
                    in_drawdown = True
                current_dd = min(current_dd, dd)
            else:  # 創新高，結束回撤
                if in_drawdown:
                    dd_abs = abs(current_dd)
                    # 只記錄超過門檻的回撤
                    if dd_abs >= min_drawdown_threshold:
                        significant_drawdowns.append(dd_abs)
                    in_drawdown = False
                    current_dd = 0
        
        # 最後一段如果還在回撤中
        if in_drawdown and current_dd < 0:
            dd_abs = abs(current_dd)
            if dd_abs >= min_drawdown_threshold:
                significant_drawdowns.append(dd_abs)
        
        if significant_drawdowns:
            avg = sum(significant_drawdowns) / len(significant_drawdowns)
            return avg, len(significant_drawdowns)
        return 0, 0
    
    def _get_best_rebalance_frequency(self, strategy):
        """計算最佳再平衡頻率"""
        if not self._traders:
            return None
        
        # 找出相同策略的所有 traders
        strategy_name = strategy.__class__.__name__
        matching_traders = {}
        
        for label, trader in self._traders.items():
            if trader.strategy.__class__.__name__ == strategy_name:
                # 計算績效指標
                history = [snap.total_value for snap in trader.portfolio_history]
                dates = [snap.timestamp for snap in trader.portfolio_history]
                
                if len(history) < 2:
                    continue
                
                initial = trader.initial_balance
                final = history[-1]
                days = (dates[-1] - dates[0]).days
                
                # 年化報酬
                annual_return = (final / initial) ** (365 / days) - 1 if days > 0 else 0
                
                # 平均回撤 (使用固定門檻 0.15)
                avg_dd, dd_count = self._calculate_average_drawdown(history, min_drawdown_threshold=0.15)
                
                # 計算分數
                score = annual_return - avg_dd
                
                matching_traders[trader.rebalance_frequency] = {
                    'frequency': trader.rebalance_frequency,
                    'annual_return': annual_return,
                    'avg_drawdown': avg_dd,
                    'drawdown_count': dd_count,
                    'score': score
                }
        
        if not matching_traders:
            return None
        
        # 找出分數最高的
        best = max(matching_traders.values(), key=lambda x: x['score'])
        
        # 中文化頻率
        freq_map = {
            'daily': '每日',
            'weekly': '每週',
            'monthly': '每月',
            'quarterly': '每季',
            'yearly': '每年'
        }
        best['frequency'] = freq_map.get(best['frequency'], best['frequency'])
        
        return best
        
    def plot_equity_curve(self, save_path: str = None, min_drawdown_label: float = 0.15):
        """
        繪製權益曲線
        
        Args:
            save_path: 圖片儲存路徑
            min_drawdown_label: 顯示回撤標籤的最小回撤比例(0-1)，例如0.15表示只顯示>=15%的回撤標籤。設為None則不顯示標籤。
        """
        if not self._traders:
            print("⚠️ No traders to plot. Run backtest first.")
            return
        
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # 收集所有曲線
        all_curves = {}
        for label, trader in self._traders.items():
            history = pd.DataFrame([
                {'date': snap.timestamp, 'value': snap.total_value}
                for snap in trader.portfolio_history
            ]).set_index('date')
            all_curves[label] = history['value']
        
        df = pd.DataFrame(all_curves)
        
        # 單曲線模式
        if len(df.columns) == 1:
            series = df.iloc[:, 0]
            ax.plot(series, linewidth=2, color='blue', label=df.columns[0])
            
            # 繪製疊加式 drawdown 陰影
            peak = series.cummax()
            drawdown_pct = (series - peak) / peak  # 負值表示回撤
            
            if min_drawdown_label is not None and min_drawdown_label > 0:
                # 計算最大回撤深度，決定要畫幾層
                max_dd = abs(drawdown_pct.min())
                num_layers = int(max_dd / min_drawdown_label) + 1
                
                # 從淺到深依序疊加繪製
                for layer in range(1, num_layers + 1):
                    threshold = -layer * min_drawdown_label
                    layer_top = peak * (1 + threshold)  # 該層的上界（前一層的下界）
                    
                    # 前一層的下界作為這層的上界
                    if layer == 1:
                        fill_top = peak  # 第一層從peak開始
                    else:
                        fill_top = peak * (1 + (-(layer-1) * min_drawdown_label))
                    
                    # 填充條件：series低於這層的上界
                    where_condition = series < fill_top
                    if where_condition.any():
                        label_text = f'Drawdown >{(layer-1)*min_drawdown_label*100:.0f}%' if layer == 1 else None
                        ax.fill_between(df.index, series, fill_top,
                                       where=where_condition,
                                       color='red', alpha=0.25, label=label_text)
            else:
                # 不分層，直接畫一層
                ax.fill_between(df.index, series, peak, 
                               where=(series < peak),
                               color='red', alpha=0.3, label='Drawdown')
            
            # 標註顯著回撤點
            if min_drawdown_label is not None:
                in_drawdown = False
                maxdd, maxdd_date = 0, None
                drawdown_labels = []
                
                for date, value in series.items():
                    if value >= peak[date]:
                        # 結束回撤期，記錄標籤
                        if in_drawdown and maxdd < -min_drawdown_label:
                            drawdown_labels.append((maxdd_date, maxdd))
                        in_drawdown = False
                        maxdd, maxdd_date = 0, None
                    else:
                        # 進入或持續回撤期
                        if not in_drawdown:
                            in_drawdown = True
                        dd_val = (value - peak[date]) / peak[date]
                        if dd_val < maxdd:
                            maxdd = dd_val
                            maxdd_date = date
                
                # 繪製標籤
                for date, dd_val in drawdown_labels:
                    ax.text(date, series[date], f"{abs(dd_val):.2%}",
                           color='red', fontsize=9, va='bottom', ha='right')
        else:
            # 多曲線模式 - 繪製區間 + 各曲線
            lower_band = df.quantile(0.25, axis=1)
            upper_band = df.quantile(0.75, axis=1)
            median = df.median(axis=1)
            
            # 繪製疊加式回撤陰影 (基於中位數)
            peak = median.cummax()
            drawdown_pct = (median - peak) / peak
            
            if min_drawdown_label is not None and min_drawdown_label > 0:
                # 計算最大回撤深度，決定要畫幾層
                max_dd = abs(drawdown_pct.min())
                num_layers = int(max_dd / min_drawdown_label) + 1
                
                # 從淺到深依序疊加繪製
                for layer in range(1, num_layers + 1):
                    threshold = -layer * min_drawdown_label
                    
                    if layer == 1:
                        fill_top = peak  # 第一層從peak開始
                    else:
                        fill_top = peak * (1 + (-(layer-1) * min_drawdown_label))
                    
                    where_condition = median < fill_top
                    if where_condition.any():
                        label_text = f'Median DD >{(layer-1)*min_drawdown_label*100:.0f}%' if layer == 1 else None
                        ax.fill_between(df.index, median, fill_top,
                                       where=where_condition,
                                       color='red', alpha=0.2, label=label_text)
            else:
                # 不分層
                ax.fill_between(df.index, median, peak, 
                               where=(median < peak),
                               color='red', alpha=0.2, label='Median Drawdown')
            
            # 繪製區間
            ax.fill_between(df.index, lower_band, upper_band,
                           color='lightblue', alpha=0.3, label='IQR Band (25%-75%)')
            ax.plot(median, color='navy', linewidth=2.5, 
                   linestyle='--', label='Median', alpha=0.8)
            
            # 標註顯著回撤點 (基於中位數)
            if min_drawdown_label is not None:
                in_drawdown = False
                maxdd, maxdd_date = 0, None
                drawdown_labels = []
                
                for date, value in median.items():
                    if value >= peak[date]:
                        if in_drawdown and maxdd < -min_drawdown_label:
                            drawdown_labels.append((maxdd_date, maxdd))
                        in_drawdown = False
                        maxdd, maxdd_date = 0, None
                    else:
                        if not in_drawdown:
                            in_drawdown = True
                        dd_val = (value - peak[date]) / peak[date]
                        if dd_val < maxdd:
                            maxdd = dd_val
                            maxdd_date = date
                
                for date, dd_val in drawdown_labels:
                    ax.text(date, median[date], f"{abs(dd_val):.2%}",
                           color='red', fontsize=9, va='bottom', ha='right')
            
            # 繪製各策略曲線
            colors = plt.cm.Set2(np.linspace(0, 1, len(df.columns)))
            for (label, series), color in zip(df.items(), colors):
                ax.plot(series, label=label, linewidth=1.5, 
                       color=color, alpha=0.7)
        
        ax.set_yscale('log')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(loc='best', fontsize=10)
        ax.set_title('Portfolio Equity Curve', fontsize=14, fontweight='bold')
        ax.set_ylabel('Portfolio Value (Log Scale)')
        ax.set_xlabel('Date')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Chart saved to: {save_path}")
        
        plt.show()
