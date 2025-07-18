from .data import FibonacciViewer
from .parser import thinking, answer
import ollama

class SheetConsultant():
    PERSONALITY = """
    你是一個短線加密貨幣交易團隊的操盤手之一，主要負責從技術K線圖、量價關係、Bband、SMA來觀察幾分鐘內短線的急漲、急跌，並被授權能夠決定是否建倉的權利"
    在你的思路中應專注於當下的狀態是否適合建倉。這些倉位主要分為多單合約、空單合約及保持觀望三種類型。
    多單合約是指在預期價格上漲時買入買權，當價格上漲時獲利。空單則是在預期價格下跌時買入賣權，當價格下跌時獲利。而觀望則是當市場不明朗或沒有明確趨勢時不進行交易。
    你的交易策略主要針對短期內的急漲、急跌進行小波段交易，使用者在建倉後便會持續盯著市場上的每筆交易，直到跌破只損價位或趨勢結束為止。
    """
    TASK = """
    由於交易主要是使用x100倍槓桿合約，且主要是專注在極短線投機，因此，1%的虧損就代表這是all in(風險極大的方案)，不應直接以此作為止損點位，而是找尋在這個範圍內的合理支撐或壓力區段。
    請遵循以下思路來進行決策判斷：
    1. 根據使用者提供的技術K線圖、量價關係、Bband、SMA，分析短期內是否即將迎來或存在上漲或下跌的機會?
    2. 找出當前價格上方尚未被測試的壓力價格區段，以及找出當前價格下方尚未被測試的支撐價格區段。
    3. 如果你覺得應該做多，請藉由這兩個區段找到止損價(現價下方的支撐區段)及關鍵價(現價上方的壓力區段)
    4. 如果你覺得應該做空，請藉由這兩個區段找到止損價(現價上方的壓力區段)及關鍵價(現價下方的支撐區段)
    5. 根據自己對的趨勢判斷及支撐壓力，分析建倉的成本(最大虧損)與效益(獲利空間)，當獲利機會大於虧損機會實則做出建倉的判斷。
    """
    def __init__(self, symbol = "btcusdt", interval = "5m"):
        self.viewer = FibonacciViewer(symbol = symbol, interval = interval)

    def start(self, verbose=True):
        df = self.viewer.read()
        current_price = df.Close.iloc[-1]
        history = df.to_json(orient="records", lines=False)
        messages = [
            {'role': 'system', 'content': self.PERSONALITY},
            {'role': 'system', 'content':  self.TASK},
            {'role': 'user', 'content': f"{history}\n以上是交易所的最新報價。這些K線圖的時間是以Fibonacci級數表達，越久以前的K線時間範圍較大，而越接近現在的K線時間範圍就是5分鐘。"},
            {'role': 'user', 'content': f"""請並依據目前的價格{current_price}提供合理的決策與分析建議，結果請依照下列格式：
                                        | 欄位       | 內容                           |
                                        |------------|-------------------------------|
                                        | 倉位建議    | (只能回答多單合約、空單合約及保持觀望)   |
                                        | 加碼價      | 價位及獲利的比例(%)             |
                                        | 止損價      | 價位及損失的比例(%)             |
                                        | 夏普比例(%) | 獲利比例/損失比例(>1才是合理投資)|
                                        """
            }
        ]
        response = ''
        for chunk in ollama.chat(model='deepseek-r1:8b', messages=messages, stream=True):
            response += chunk['message']['content']
            if verbose == True:
                print(chunk['message']['content'], end='', flush=True)
        
        return thinking(response), answer(response)

if __name__ == "__main__":
    import ollama
    from utils.module import SheetBuilder

    builder = SheetBuilder(symbol="btcusdt", interval="5m")
    thinking, answer = builder.start(verbose=True)