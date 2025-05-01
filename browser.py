import os
import asyncio
from browser_use import Agent
from langchain_ollama import ChatOllama

# Another question: Go to https://aleksandarhaber.com and find the title of this website

async def run_search() -> str:
    agent = Agent(
        task="What is the current temperature in Boston, Massachusetts?",
        llm=ChatOllama(
            model="qwen2.5:7b",
            num_ctx=32000,
        ),
        max_actions_per_step=3,
		tool_call_in_content=False,
    )

    result = await agent.run(max_steps=15)
    return result


async def main():
    result = await run_search()
    print("\n\n", result)


if __name__ == "__main__":
    asyncio.run(main())