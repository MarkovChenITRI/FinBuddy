import gradio as gr
from PIL import Image
from PortfolioLab_Parser.utils import IXIC_Parsor
import requests
import pandas as pd
class Functions():
    def __init__(self):
        self.detail_col = ['Name', 'beta', 'Premium', 'forwardPE', 'shortRatio', 'currentPrice', 'targetLowPrice', 'targetHighPrice']

    def is_internet_connected(self):
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def update_dataframe(self, positive_reward):
        if not self.is_internet_connected():
            gr.Info("Internet not are not connected.", duration=5)
            return None
        else:
            df = self.df.copy()
            print(df.shape)
            if positive_reward:
                df = df[df['Premium'] > 1]
            return df.loc[:, self.detail_col]

    def analysis_portfolio(self, portfolio_list, mail_address, progress=gr.Progress()):
        if not self.is_internet_connected():
            gr.Info("Internet not are not connected.", duration=5)
            return None, None, None
        else:
            print('Mail Address:', mail_address)
            portfolio_list = {i: portfolio_list[i]["default"].strip('\n').split(' | ') for i in portfolio_list}

            parsor = IXIC_Parsor(portfolio_list = portfolio_list, tqdm_provider=progress.tqdm)
            
            self.df = parsor.fit()
            categories = []
            for code in self.df.index:
                for category in portfolio_list:
                    if code in portfolio_list[category]:
                        categories.append(category); break
            self.df['categories'] = categories
            self.df['Name'] = self.df.index
            self.df['Premium'] = self.df['Premium'].round(2)
            return self.df, self.df.loc[:, self.detail_col], gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)

func = Functions()
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            gr.Image(Image.open('./assets/images/linebot.png'),
                     label="LineBot QR Code", 
                     show_share_button = False,
                     show_download_button = False,
                     type="pil")
            paramviewer = gr.ParamViewer( 
                {
                    "Silicon": {
                        "default": "NVDA | ARM | INTC | IBM | META | AMD | TXN | QCOM | AVGO | MU\n",
                        "type": '\n',
                        "description": "Focused on the development and manufacturing of high-performance chips to support computational needs for artificial intelligence, graphics processing, high-speed communication, and data storage."
                    },
                    "Robotics": {
                        "default": 'BSX | TSLA\n',
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
                header='Portfolio List',
            )
            user_input = gr.Textbox(label="Enter E-mail:")
            submit_button = gr.Button("Start/Subscrbe")

        with gr.Column(scale=12):
            gr.Markdown(
                """
                # FinBuddy
                FinBuddy 是一個幫助你管理金融投資組合的AI助理. 您可以為自己所屬的產業別設定需被關注的股票清單，他會從中為您篩選出當前行情中適合投資的股票。(*試用版無法新增/刪除標的)

                注意! 這是一個動態調整的投資策略，你可以透過Line機器人獲取即時的推播通知。
                """
            )
            with gr.Tab("Overview"):
                scatter_plot = gr.ScatterPlot(x='Premium', y='beta', color='categories', height=420)

            with gr.Tab("Details"):
                positive_reward = gr.Checkbox(label="Positive Reward", value=False, interactive=False)
                dataframe = gr.DataFrame()
            with gr.Tab("Planer"):
                with gr.Row():
                    profit_factor = gr.Slider(value=0, label='Risk Premium for $1', minimum=0, maximum=100, step=1, interactive=False)
                    risk_factor = gr.Slider(value=100, label='Risk Capacity for $1', minimum=0, maximum=100, step=1, interactive=False)
                
    positive_reward.change(func.update_dataframe, 
                        inputs=[positive_reward],
                        outputs=dataframe)
    submit_button.click(func.analysis_portfolio, 
                        inputs=[paramviewer, user_input], 
                        outputs=[scatter_plot, dataframe, profit_factor, risk_factor, positive_reward])
demo.launch()