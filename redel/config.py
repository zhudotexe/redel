import os
from pathlib import Path

# ==== core ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
# if gpt-4 (not variant models) should use a different org id
OPENAI_ORG_ID_GPT4 = os.getenv("OPENAI_ORG_ID_GPT4", OPENAI_ORG_ID)

# caching of embeddings, etc
REDEL_CACHE_DIR = Path(os.getenv("REDEL_CACHE", "~/.cache/redel")).expanduser()
REDEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ==== voice ====
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

# ==== email ====
EMAIL_HOST = os.getenv("EMAIL_HOST")  # a string like mailserv.zhu.codes:465
EMAIL_FROM = os.getenv("EMAIL_FROM")  # the email address to send email from
EMAIL_PASS = os.getenv("EMAIL_PASS")  # the password for the email account
