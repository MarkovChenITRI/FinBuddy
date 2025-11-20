import requests
import yfinance as yf
import numpy as np
import pandas as pd
from scipy.stats import linregress
from tqdm import tqdm
from scipy.signal import find_peaks
from sklearn.linear_model import LogisticRegression
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)


class TradingViewWatchlist:
    """TradingView 投資組合清單"""
    
    def __init__(self, watchlist_id: str = "118349730", session_id: str = 'b379eetq1pojcel6olyymmpo1rd41nng'):
        self.watchlist_id = watchlist_id
        self.session_id = session_id
        self.result = {}
        self.providers = {}
        self.industries = {}
        self._fetch_watchlist()
        
    def _fetch_watchlist(self):
        """從 TradingView 取得投資組合清單"""
        url = f'https://in.tradingview.com/api/v1/symbols_list/custom/{self.watchlist_id}'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cookie': f'sessionid={self.session_id}',
            'origin': 'https://in.tradingview.com',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        symbols = requests.get(url, headers=headers).json()["symbols"]
        result = {}
        current_key = None
        
        for item in symbols:
            if "###" in item:
                current_key = item.strip("###\u2064")
                result[current_key] = {}
            elif current_key:
                provider, code = item.split(":", 1)
                if provider not in result[current_key]:
                    result[current_key][provider] = []
                    
                if provider in ['NASDAQ', 'NYSE']:
                    result[current_key][provider].append(code)
                elif provider in ['TWSE']:
                    result[current_key][provider].append(f"{code}.TW")
        
        self.result = result
        self.providers = {
            code: provider 
            for industry in result 
            for provider in result[industry] 
            for code in result[industry][provider]
        }
        self.industries = {
            code: industry 
            for industry in result 
            for provider in result[industry] 
            for code in result[industry][provider]
        }
        
    def todict(self):
        return self.result
        
    def tolist(self):
        return [
            code
            for industry in self.result
            for provider in self.result[industry]
            for code in self.result[industry][provider]
        ]
        
    def get_provider(self, code):
        return self.providers.get(code)
        
    def get_industry(self, code):
        return self.industries.get(code)


class MarketDataProvider:
    """市場數據提供者 - 負責數據下載與指標計算"""
    
    def __init__(self, watchlist_id: str = None, session_id: str = None):
        if watchlist_id and session_id:
            self.watchlist = TradingViewWatchlist(watchlist_id, session_id)
        else:
            self.watchlist = TradingViewWatchlist()  # 使用預設值
            
    def get_watchlist(self):
        """取得 watchlist 物件"""
        return self.watchlist
        
    def get_history_with_unified_datetime(self, ticker: str, period: str = "15y", interval: str = "1d") -> pd.DataFrame:
        """下載股票歷史數據"""
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        df = df.tz_localize(None)
        df = df.sort_index()
        return df
        
    def calculate_rainbow_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算彩虹圖波段"""
        df = df.copy()
        
        # 對數-對數回歸
        df['days'] = (df.index - df.index.min()).days
        df = df[df['days'] > 0]
        df['ln_days'] = np.log(df['days'])
        df['log10_price'] = np.log10(df['Close'])
        
        a, b = np.polyfit(df['ln_days'], df['log10_price'], deg=1)
        df['log10_trend'] = a * df['ln_days'] + b
        df['resid'] = df['log10_price'] - df['log10_trend']
        
        # 計算分位數波段
        quantiles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        resid_levels = np.quantile(df['resid'], quantiles)
        
        for i, rl in enumerate(resid_levels):
            band_log10 = df['log10_trend'] + rl
            df[f'Band_{i+1}'] = 10 ** band_log10
            
        df['Trend'] = 10 ** df['log10_trend']
        return df
        
    def calculate_statistical_indicators(self, df: pd.DataFrame, reverse: bool = False) -> pd.DataFrame:
        """計算波動率、Beta、權重"""
        df = df.copy()
        prices = df['Close'].astype(float)
        band_keys = sorted([c for c in df.columns if c.startswith('Band_')],
                          key=lambda k: int(k.split('_')[1]))
        
        # 計算波動率
        rets = np.log(prices).diff()
        vol = rets.expanding().std(ddof=0) * np.sqrt(252)
        vol.iloc[0] = np.nan
        
        # 計算區段
        segments = []
        n_bands = len(band_keys)
        for i, p in enumerate(prices.to_numpy()):
            seg = None
            for j in range(n_bands - 1):
                lower = df[band_keys[j]].iat[i]
                upper = df[band_keys[j + 1]].iat[i]
                if lower <= p < upper:
                    seg = j + 1
                    break
            if seg is None:
                seg = 0 if p < df[band_keys[0]].iat[i] else n_bands
            segments.append(seg)
        
        df['segments'] = segments
        if reverse:
            df['segments'] = 9 - df['segments']
            
        df['volatilities'] = vol.values
        
        # 計算 Beta 與權重
        vol_clean = vol.replace(0, np.nan)
        cum_avg = vol_clean.expanding().mean()
        cum_max = vol_clean.expanding().max()
        
        base_weights = 1.0 / cum_avg
        betas = vol / cum_max
        betas = betas.where(cum_max > 0)
        
        df['base_weights'] = base_weights.ffill()
        df['betas'] = betas.ffill()
        
        return df
        
    def calculate_sharpe(self, df: pd.DataFrame, price_col: str = 'Close', 
                        sharpe_window: int = 365, risk_free_rate: float = 0.04) -> pd.DataFrame:
        """計算夏普比率"""
        df = df.copy()
        df["Returns"] = df[price_col].pct_change()
        daily_rf_rate = risk_free_rate / sharpe_window
        excess_returns = df["Returns"] - daily_rf_rate
        rolling_mean = excess_returns.rolling(sharpe_window).mean()
        rolling_std = excess_returns.rolling(sharpe_window).std()
        df["Sharpe"] = rolling_mean / rolling_std * np.sqrt(sharpe_window)
        return df
        
    def calculate_slope(self, series: pd.Series, slope_window: int = 365) -> pd.Series:
        """計算斜率"""
        slopes = [np.nan] * slope_window
        for i in range(slope_window, len(series)):
            x = np.arange(slope_window)
            y = series[i-slope_window:i]
            slope, _, _, _, _ = linregress(x, y)
            slopes.append(slope)
        return pd.Series(slopes, index=series.index)
        
    def get_stock_full_info(self, ticker: str, sharpe_window: int = 365) -> pd.DataFrame:
        """取得單一股票完整資訊"""
        df = self.get_history_with_unified_datetime(ticker)
        df = self.calculate_rainbow_bands(df)
        df = self.calculate_statistical_indicators(df)
        df = self.calculate_sharpe(df, price_col='Close', sharpe_window=sharpe_window)
        return df
        
    def download_stock_data(self, df: pd.DataFrame, watchlist: TradingViewWatchlist, 
                           sharpe_window: int = 365) -> pd.DataFrame:
        """下載所有股票數據"""
        watchlist_dict = watchlist.todict()
        
        for industry in tqdm(watchlist_dict, desc="Downloading data"):
            for provider in watchlist_dict[industry]:
                for code in watchlist_dict[industry][provider]:
                    try:
                        temp_df = self.get_stock_full_info(code, sharpe_window=sharpe_window)
                        df[f'{code}_Close'] = temp_df['Close']
                        df[f'{code}_Sharpe'] = temp_df['Sharpe']
                        df[f'{code}_Base'] = temp_df['base_weights']
                        df[f'{code}_Volatility'] = temp_df['volatilities']
                        df[f'{code}_Beta'] = temp_df['betas']
                    except Exception as e:
                        print(f"⚠️ Failed to download {code}: {e}")
                        
        return df.ffill()
        
    def integrate_industry_metrics(self, df: pd.DataFrame, watchlist: TradingViewWatchlist, 
                                   ma_period: int, slope_window: int = 365) -> pd.DataFrame:
        """整合產業指標"""
        watchlist_dict = watchlist.todict()
        
        for industry in tqdm(watchlist_dict, desc="Integrating metrics"):
            sharpe_matrix = pd.DataFrame()
            for provider in watchlist_dict[industry]:
                for code in watchlist_dict[industry][provider]:
                    if f'{code}_Sharpe' in df.columns:
                        sharpe_matrix[code] = df[f'{code}_Sharpe']
                        
            df[f'{industry}_Integrated_Sharpe'] = sharpe_matrix.mean(axis=1, skipna=True)
            df[f'{industry}_Sharpe_Slope'] = self.calculate_slope(df[f'{industry}_Integrated_Sharpe'], slope_window=slope_window)
            df[f'{industry}_MA_Short'] = df[f'{industry}_Sharpe_Slope'].rolling(window=ma_period).mean()
            df[f'{industry}_MA_Long'] = df[f'{industry}_Sharpe_Slope'].rolling(window=ma_period * 4).mean()
            
        return df
        
    def find_turning_points(self, df: pd.DataFrame, watchlist: TradingViewWatchlist) -> pd.DataFrame:
        """偵測高低轉折點"""
        watchlist_dict = watchlist.todict()
        
        for industry in tqdm(watchlist_dict, desc="Finding change points"):
            dir_series = df[f"{industry}_MA_Short"] > df[f"{industry}_MA_Long"]
            slope = df[f"{industry}_Sharpe_Slope"]
            highs = [i for i in find_peaks(slope)[0] if dir_series.iloc[i]]
            lows = [i for i in find_peaks(-slope)[0] if not dir_series.iloc[i]]
            cross = np.where(dir_series.shift(1) != dir_series)[0]
            
            hcp, lcp, used_h, used_l = [], [], set(), set()
            for j in cross:
                if j < 1:
                    continue
                if dir_series.iloc[j - 1]:
                    prev = [h for h in highs if h < j and h not in used_h]
                    if prev:
                        h = prev[-1]
                        hcp.append(h)
                        used_h.add(h)
                else:
                    prev = [l for l in lows if l < j and l not in used_l]
                    if prev:
                        l = prev[-1]
                        lcp.append(l)
                        used_l.add(l)
            
            cp = pd.Series(index=df.index, dtype="float")
            cp.iloc[hcp] = 1
            cp.iloc[lcp] = 0
            df[f'{industry}_CP'] = cp.ffill()
            
        return df
        
    def generate_crossover_state(self, s: pd.Series, l: pd.Series) -> pd.Series:
        """產生交叉狀態"""
        state = pd.Series(index=s.index, dtype=int)
        cur = int(s.iloc[0] > l.iloc[0])
        state.iloc[0] = cur
        
        for i in range(1, len(s)):
            if cur and s.iloc[i - 1] > l.iloc[i - 1] and s.iloc[i] <= l.iloc[i]:
                cur = 0
            elif not cur and s.iloc[i - 1] < l.iloc[i - 1] and s.iloc[i] >= l.iloc[i]:
                cur = 1
            else:
                cur = int(s.iloc[i] > l.iloc[i])
            state.iloc[i] = cur
            
        return state
        
    def summary_overall_state(self, df: pd.DataFrame, watchlist: TradingViewWatchlist) -> pd.DataFrame:
        """彙總整體狀態"""
        watchlist_dict = watchlist.todict()
        df['Trend'] = 0
        
        for industry in tqdm(watchlist_dict, desc="Summary overall state"):
            df[f"{industry}_Crossover_State"] = self.generate_crossover_state(
                df[f"{industry}_MA_Short"], 
                df[f"{industry}_MA_Long"]
            )
            df['Trend'] += df[f"{industry}_Crossover_State"]
            
        df['Trend'] = df['Trend'] / len(watchlist_dict.keys())
        return df
        
    def build_decline_prediction(self, df: pd.DataFrame, watchlist: TradingViewWatchlist) -> pd.DataFrame:
        """建立下跌預測模型"""
        watchlist_dict = watchlist.todict()
        
        data = pd.concat([
            pd.DataFrame({
                'Industry': industry,
                'Trend': df['Trend'],
                'State': df[f'{industry}_Crossover_State'],
                'Decline': df[f'{industry}_CP']
            }) for industry in watchlist_dict
        ]).dropna()
        
        model = LogisticRegression().fit(data[['Trend', 'State']], data['Decline'])
        
        for industry in watchlist_dict:
            X = pd.DataFrame({
                'Trend': df['Trend'], 
                'State': df[f'{industry}_Crossover_State']
            })
            df[f'{industry}_Decline'] = model.predict_proba(X)[:, 1]
            
        return df
        
    def build_portfolio_data(self, watchlist: TradingViewWatchlist, 
                            sharpe_window: int = 365, 
                            slope_window: int = 365, 
                            ma_period: int = 30) -> pd.DataFrame:
        """
        建立完整投資組合數據
        
        Args:
            watchlist: TradingView 投資組合清單
            sharpe_window: 計算 Sharpe 比率的視窗大小 (預設: 365天)
            slope_window: 計算斜率的視窗大小 (預設: 365天)
            ma_period: 產業移動平均的短期週期 (預設: 30天, 長期為 30*4=120天)
        """
        # 以大盤指數為基準建立時間序列
        df = self.get_stock_full_info('^IXIC', sharpe_window=sharpe_window)
        
        # 下載個股數據
        df = self.download_stock_data(df, watchlist, sharpe_window=sharpe_window)
        
        # 整合產業指標
        df = self.integrate_industry_metrics(df, watchlist, ma_period=ma_period, slope_window=slope_window)
        
        # 偵測轉折點
        df = self.find_turning_points(df, watchlist)
        
        # 彙總整體狀態
        df = self.summary_overall_state(df, watchlist)
        
        # 建立下跌預測
        df = self.build_decline_prediction(df, watchlist)
        
        # 清理數據
        df = df.ffill().iloc[912:, :]
        
        return df
