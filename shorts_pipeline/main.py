import os, json, importlib
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

sources = [
    ("google_trends", "fetch_google_trends"),
    ("wikipedia_today", "fetch_wikipedia_today"),
]
raw_topics = []
for mod, fn in sources:
    module = importlib.import_module(f"collectors.{mod}")
    raw_topics += getattr(module, fn)()
raw_topics = list(dict.fromkeys(raw_topics))

from utils.ranking_prompt import build_prompt
prompt = build_prompt(raw_topics, n_select=5)

response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content": prompt}],
    temperature=0.7
)

best_topics = json.loads(
    response.choices[0].message.content.replace("```yaml","").replace("```","")
)

print("=== GPT が選んだトップテーマ ===")
for t in best_topics:
    print("-", t)
