import mplfinance as mpf

def plot(df):
    df_plot = df.set_index('Datetime').copy()
    apds = []

    if 'UpperBand' in df.columns and 'LowerBand' in df.columns:
        apds += [
            mpf.make_addplot(df_plot['UpperBand'], color='orange', width=0.8),
            mpf.make_addplot(df_plot['LowerBand'], color='orange', width=0.8)
        ]

    if 'OuterUpper' in df.columns and 'OuterLower' in df.columns:
        apds += [
            mpf.make_addplot(df_plot['OuterUpper'], color='red', width=0.6, linestyle='dotted'),
            mpf.make_addplot(df_plot['OuterLower'], color='red', width=0.6, linestyle='dotted')
        ]

    if 'SMA' in df.columns:
        apds += [
            mpf.make_addplot(df_plot['SMA'], color='blue', width=1.2, linestyle='solid')
        ]

    return mpf.plot(
        df_plot[['Open', 'High', 'Low', 'Close']],
        type='candle',
        style='charles',
        title='Compressed K-Line with Bollinger Bands & SMA',
        volume=False,
        addplot=apds
    )