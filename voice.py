"""Listen along to the websocket and narrate any assistant root message contents."""

import asyncio
import logging

import aiohttp
import elevenlabs
from kani import ChatRole, Kani
from kani.engines.openai import OpenAIEngine

from kanpai import events
from kanpai.config import ELEVEN_API_KEY, ELEVEN_VOICE_ID

lock = asyncio.Lock()
log = logging.getLogger("voice")

# 11labs
voice_settings = elevenlabs.VoiceSettings(stability=0.33, similarity_boost=1.0, style=0.0, use_speaker_boost=False)
voice = elevenlabs.Voice(voice_id=ELEVEN_VOICE_ID, settings=voice_settings)
elevenlabs.set_api_key(ELEVEN_API_KEY)

# openai
engine = OpenAIEngine(model="gpt-4")


async def handle_message(content: str):
    # transform to more speakable version
    log.info(f"Got content: {content}")
    ai = Kani(engine)
    transformed_content = await ai.chat_round_str(
        "Please rewrite the following message to be suitable for speaking out load, while maintaining"
        f' its personality. If no change is needed, say "No change."\n\nMessage\n=======\n{content}'
    )
    log.info(f"Transformed: {transformed_content}")
    if transformed_content.lower().startswith("no change"):
        transformed_content = content
    # generate speech and stream it
    async with lock:
        asyncio.get_event_loop().run_in_executor(None, tts, transformed_content)


def tts(text: str):
    stream = elevenlabs.generate(text=text, voice=voice, model="eleven_multilingual_v2", stream=True)
    audio = elevenlabs.stream(stream)
    return audio


async def main():
    """Connect to the websocket and dispatch any root messages with content to the tts entrypoint."""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("http://127.0.0.1:8000/api/ws") as ws:
            log.info("WS connected")
            while True:
                msg = await ws.receive_json()
                if msg["type"] != "root_message":
                    continue
                event = events.RootMessage.model_validate(msg)
                if event.msg.role == ChatRole.ASSISTANT and event.msg.content:
                    asyncio.create_task(handle_message(event.msg.content))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
