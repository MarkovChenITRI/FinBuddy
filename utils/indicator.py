def calculate_bbands(df, window=20, std_multiplier=2, outer_multiplier=1.5):
    df = df.copy()
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['STD'] = df['Close'].rolling(window=window).std()

    df['UpperBand'] = df['SMA'] + std_multiplier * df['STD']
    df['LowerBand'] = df['SMA'] - std_multiplier * df['STD']

    df['BandWidth'] = df['UpperBand'] - df['LowerBand']
    df['BandSTD'] = df['BandWidth'].rolling(window=window).std()

    df['OuterUpper'] = df['UpperBand'] + df['BandSTD'] * outer_multiplier
    df['OuterLower'] = df['LowerBand'] - df['BandSTD'] * outer_multiplier

    return df