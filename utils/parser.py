import re

def thinking(text):
    think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    think = think_match.group(1).strip() if think_match else None
    return think

def answer(text):
    answer_match = re.search(r"\*\*Solution:\*\*(.*)", text, re.DOTALL)
    answer = answer_match.group(1).strip() if answer_match else None
    return answer