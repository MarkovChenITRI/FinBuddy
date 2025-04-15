import gradio as gr
from PIL import Image

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            gr.Image(Image.open('./assets/images/linebot.png'),
                     label="LineBot QR Code", 
                     show_share_button = False,
                     show_download_button = False,
                     type="pil")
            gr.ParamViewer( 
                {
                    "Silicon": {
                        "default": "NVDA | ARM | INTC | IBM | META | AMD | TXN | QCOM | AVGO | MU\n",
                        "type": '\n',
                        "description": "Focused on the development and manufacturing of high-performance chips to support computational needs for artificial intelligence, graphics processing, high-speed communication, and data storage."
                    },
                    "Robotics": {
                        "default": 'BSX | TELA\n',
                        "type": '\n',
                        "description": 'Promotes the design and application of robotics, including automated systems for medical surgeries and autonomous mechanical equipment in industrial production, enhancing efficiency and precision.'
                    },
                    "Fabs": {
                        "default": 'TSM | ASML | AMAT | INTC | AMKR\n',
                        "type": '\n',
                        "description": 'Responsible for semiconductor wafer manufacturing, material processing, and testing services, utilizing advanced process technologies to meet the production demands of electronic products.'
                    },
                    "AI": {
                        "default": 'XOVR | MSFT | META | GOOG\n',
                        "type": '\n',
                        "description": 'Focused on the development of artificial intelligence algorithms and systems, driving applications in natural language processing, autonomous driving, intelligent assistants, and business analytics.'
                    },
                    "IT/OT": {
                        "default": 'MSFT | AMZN | GOOG\n',
                        "type": '\n',
                        "description": 'Combining cloud computing with industrial control technologies to provide intelligent solutions, supporting smart factories, energy management, and operational efficiency improvement.'
                    },
                    "PDA": {
                        "default": 'AAPL | DELL | HPQ | META\n',
                        "type": '\n',
                        "description": 'Focused on designing portable devices that provide functions for daily management, digital communication, and productivity enhancement, integrating artificial intelligence to improve user experience.'
                    }
                },
                header='Portfolio List (Locked)',
            )
        with gr.Column(scale=12):
            gr.Markdown(
                """
                # FinBuddy
                FinBuddy 是一個幫助你管理金融投資組合的AI助理. 您可以為自己所屬的產業別設定需被關注的股票清單，他會從中為您篩選出當前行情適合投資的股票。

                注意! 這是一個中長期動態調整的策略。
                """
            )
demo.launch()