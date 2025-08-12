from crewai import Agent

translator_agent = Agent(
    role="Translator",
    goal="Translate technical documentations from English to other languages",
    backstory="You are a translator. You are given a chunk of a file from a technical documentation and you need to translate it into other languages.",
    verbose=False,
    llm="gpt-4.1",
    # llm="anthropic/claude-sonnet-4-20250514",
)
