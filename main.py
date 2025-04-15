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
        with gr.Column(scale=12):
            gr.Markdown(
                """
                # FinBuddy
                FinBuddy 是一個幫助你管理投資組合的助理.
                """
            )
demo.launch()