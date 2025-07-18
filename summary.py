from utils.module import SheetConsultant

builder = SheetConsultant(symbol="btcusdt", interval="5m")
thinking, answer = builder.start(verbose=True)