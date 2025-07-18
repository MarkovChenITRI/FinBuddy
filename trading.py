from utils.tools import BUY, SELL

messages = [{'role': 'user', 'content': 'Buy 5 BTC.'}]
for call in ollama.chat(model='llama3.2:latest', messages=messages, tools=[BUY, SELL])['message']['tool_calls']:
    print(call['function']['name'], call['function']['arguments'])