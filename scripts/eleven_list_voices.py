import os

import elevenlabs

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

elevenlabs.set_api_key(ELEVEN_API_KEY)
for voice in elevenlabs.voices().voices:
    print(f"{voice.name} ({voice.voice_id})")
