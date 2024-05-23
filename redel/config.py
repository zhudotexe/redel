import os

# ==== core ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if gpt-4 (not variant models) should use a different org id
OPENAI_ORG_ID_GPT4 = os.getenv("OPENAI_ORG_ID_GPT4", os.getenv("OPENAI_ORG_ID"))

# ==== voice ====
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

# ==== email ====
EMAIL_HOST = os.getenv("EMAIL_HOST")  # a string like mailserv.zhu.codes:465
EMAIL_FROM = os.getenv("EMAIL_FROM")  # the email address to send email from
EMAIL_PASS = os.getenv("EMAIL_PASS")  # the password for the email account
