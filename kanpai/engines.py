import os

from kani.engines.openai import OpenAIEngine

api_key = os.getenv("OPENAI_API_KEY")
engine = OpenAIEngine(api_key=api_key, model="gpt-4", temperature=0.8, top_p=0.95)
long_engine = OpenAIEngine(api_key=api_key, model="gpt-4-32k", temperature=0.1)
