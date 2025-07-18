import pandas as pd
from .indicator import calculate_bbands

class FibonacciViewer():
    def __init__(self, symbol="btcusdt", interval="5m", fib=7):
        self.symbol = symbol
        self.interval = interval
        self.fib = fib
        self.log_path = f"./logs/{symbol}_{interval}.csv"

    def read(self, end_date=None):
        df = pd.read_csv(self.log_path, low_memory=False)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df = df.sort_values('Datetime').groupby('Datetime').last().reset_index()
        df = calculate_bbands(df)

        if end_date is not None:
            end_date = pd.to_datetime(end_date)
            df = df[df['Datetime'] <= end_date]

        fib_val = self._fibonacci_recursive(self.fib)
        print(f"📌 保留尾端最後 {fib_val} 筆原始樣本（未壓縮）")
        print(f"🔁 遞回壓縮剩餘前段資料，起始 Fibonacci index: {self.fib}\n")

        # 尾部保留未壓縮樣本 + 技術指標欄位
        preserved = df.iloc[-fib_val:].copy()
        preserved_df = preserved[['Datetime', 'Open', 'Close', 'High', 'Low',
                                  'SMA', 'STD', 'UpperBand', 'LowerBand',
                                  'BandWidth', 'BandSTD', 'OuterUpper', 'OuterLower']].copy()
        preserved_df['depth'] = -1
        preserved_df['fib_count'] = fib_val
        preserved_df['unit_size'] = 1
        
        # 前段壓縮
        compressed_df = self._compress_recursive(df.iloc[:-fib_val], self.fib)

        # 合併並排序
        combined = pd.concat([compressed_df, preserved_df], ignore_index=True)
        combined = combined.sort_values('Datetime').reset_index(drop=True)
        del combined['depth'], 	combined['fib_count'], 	combined['unit_size'], 	combined['STD']
        
        # 將 Datetime 轉換為字串格式
        combined['Datetime'] = combined['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"📊 最終樣本總數：{len(combined)} 筆（含壓縮與未壓縮）")
        print(f"📊 當前最新價格：{combined.Close.iloc[-1]}")
        return combined

    def _compress_recursive(self, df, fib_seed, depth=0, results=None):
        if results is None:
            results = []

        fib_n = self._fibonacci_recursive(fib_seed + depth)
        unit = 4 * (2 ** depth)

        if fib_n > len(df):
            return pd.DataFrame(results)

        segment = df.iloc[-fib_n:]
        for i in range(0, len(segment) - unit + 1, unit):
            sample = segment.iloc[i:i + unit]
            summary = {
                'Datetime': sample['Datetime'].iloc[-1],
                'Open': sample['Open'].iloc[0],
                'Close': sample['Close'].iloc[-1],
                'High': sample['High'].max(),
                'Low': sample['Low'].min(),
                'depth': depth,
                'fib_count': fib_n,
                'unit_size': unit
            }
            results.append(summary)

        remaining_df = df.iloc[:-fib_n]
        return self._compress_recursive(remaining_df, fib_seed, depth + 1, results)

    def _fibonacci_recursive(self, n):
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        return self._fibonacci_recursive(n - 1) + self._fibonacci_recursive(n - 2)

if __name__ == "__main__":
    from visualizer import plot

    viewer = FibonacciViewer()
    df = viewer.read()
    plot(df)