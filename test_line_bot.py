"""
測試 demo.py 的本地版本（不需要 functions_framework）
"""

from libs import SimulatedMarket, MaxSharpeStrategy, LinearProgrammingStrategy
from linebot import LineBotApi
from linebot.models import TextSendMessage


# Line Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = 'Es+feMvp7Uwg+nIcgB66iAKWVD1dOKRcXzYwPmSbko+b0Vf21iko3s7dRwEFX1tfToR8mrW78XUACEd/uyecCF/Uqd9LgvkchpPEPiODdX4L8BU4b6pXHzFvlDoAfsP9xIFSMG+rmVzQURS+7uBnegdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'Udba3ff0abbe6607af5a5cfc2e2ddc8a1'


def send_line_message(text):
    """發送 Line 訊息"""
    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        print("✅ Line 訊息發送成功")
        return True
    except Exception as e:
        print(f"❌ Line 訊息發送失敗: {e}")
        return False


def main():
    """主函數 - 生成交易建議並發送到 Line"""
    print("=" * 70)
    print("🚀 FinBuddy Trading System - Line Bot 測試")
    print("=" * 70)
    
    # 初始化市場模擬器
    print("\n🔄 初始化市場模擬器...")
    simulator = SimulatedMarket(
        watchlist_id="118349730",
        session_id="b379eetq1pojcel6olyymmpo1rd41nng"
    )
    
    # 建立數據
    print("📊 建立投資組合數據...")
    simulator.build_portfolio_data(
        sharpe_window=252, 
        slope_window=365, 
        ma_period=30
    )
    
    # 生成交易建議
    print("\n💡 生成交易建議...")
    strategy = MaxSharpeStrategy(topk=10)
    recommendation = simulator.get_trading_recommendation(strategy)
    
    # 顯示建議
    print("\n" + "=" * 70)
    print("📋 今日交易建議：")
    print("=" * 70)
    print(recommendation)
    print("=" * 70)
    
    # 發送到 Line
    print("\n📤 發送訊息到 Line...")
    success = send_line_message(recommendation)
    
    if success:
        print("\n✅ 完成！訊息已發送到 Line Bot")
    else:
        print("\n⚠️ 訊息生成成功，但 Line 發送失敗")
        print("請檢查：")
        print("  1. LINE_CHANNEL_ACCESS_TOKEN 是否正確")
        print("  2. LINE_USER_ID 是否正確")
        print("  3. 網路連線是否正常")


if __name__ == "__main__":
    main()
