from requests.models import encode_multipart_formdata
import discord as D
from discord import app_commands
from pathlib import Path

from pydub import AudioSegment
from RSD import config, generated_config

import os
from dotenv import load_dotenv
import logging
import json
import requests
import asyncio

BOT_TESTING = 1286311062710390887

RSD_SERVER = "http://localhost:8080/command"
HEADERS = {"Content-Type": "application/json"}

MODELS = list(config.VOICE_MODELS.keys())
AUDIOS = list(generated_config.AUDIOS)

intents = D.Intents.default()
intents.message_content = True
intents.members = True

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_RSD")
GUILD_TOKEN = int(os.getenv("DISCORD_GUILD", 0))


# logging.basicConfig(level=logging.DEBUG)


class MyClient(D.Client):
    def __init__(self, *, intents: D.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.synced = False

    async def on_ready(self):
        print(f"Bot is ready. Logged in as {self.user}")
        if not self.synced:  # Only sync if we haven't already
            print("not synced")
            try:
                print(f"Attempting to sync commands to guild: {GUILD_TOKEN}")
                synced = await self.tree.sync(guild=D.Object(id=GUILD_TOKEN))
                print(f"Synced {len(synced)} commands")
                self.synced = True
            except Exception as e:
                logging.error(f"Failed to sync commands: {e}")

        for guild in self.guilds:
            print(f"Connected to guild: {guild.id}")
            if guild.id == GUILD_TOKEN:
                try:
                    cmds = await self.tree.fetch_commands(
                        guild=D.Object(id=GUILD_TOKEN)
                    )
                    print(f"Fetched {len(cmds)} commands for guild {GUILD_TOKEN}")
                    for cmd in cmds:
                        print(f"Command: {cmd.name}")
                except Exception as e:
                    print(f"Failed to fetch commands: {e}")


client = MyClient(intents=intents)


@client.tree.command(
    name="rsd_request",
    description="Send a request to RSD server",
    guild=D.Object(id=GUILD_TOKEN),
)
@app_commands.describe(
    delay="Delay in seconds",
    text="Text for TTS",
    repeat="Repeat the TTS",
    model_name="Model name for TTS",
    start="Sound before msg",
    end="Sound after msg",
    background="Background sound",
)
@app_commands.choices(
    model_name=[app_commands.Choice(name=key, value=key) for key in MODELS],
    start=[app_commands.Choice(name=key, value=key) for key in AUDIOS],
    end=[app_commands.Choice(name=key, value=key) for key in AUDIOS],
    background=[app_commands.Choice(name=key, value=key) for key in AUDIOS],
)
async def rsd_request(
    interaction: D.Interaction,
    channel: D.TextChannel,
    heading: str,
    delay: int,
    text: str,
    repeat: bool,
    model_name: app_commands.Choice[str],
    start: app_commands.Choice[str] = None,
    end: app_commands.Choice[str] = None,
    background: app_commands.Choice[str] = None,
):
    start_value = generated_config.AUDIOS["_begin"] if start is None else start.value
    end_value = generated_config.AUDIOS["_end"] if end is None else end.value
    background_value = None if background is None else background.value

    payload = {
        "heading": heading,
        "delay_s": str(delay),
        "items": [
            {"type": "audio", "path": start_value},
            {
                "type": "tts",
                "text": text,
                "repeat": repeat,
                "background_path": background_value,
                "model_name": model_name.value,
            },
            {"type": "audio", "path": end_value},
        ],
        "pending": True if delay > 0 else False,
    }

    print(repr(json.dumps(payload)))

    try:
        await (
            interaction.response.defer()
        )  # Defer the response as file upload might take time

        response = requests.post(RSD_SERVER, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()

        files_to_upload = response.json()["tts_file"]
        await upload_audio_files(client, channel, heading, files_to_upload, [text])

        await interaction.followup.send(
            "Files have been uploaded to the specified channel."
        )

        # await interaction.response.send_message(
        #     f"Command sent successfully. Status code: {response.status_code}\nfile: {response.json()['tts_file']}"
        # )
    except requests.RequestException as e:
        await interaction.response.send_message(f"Error sending command: {str(e)}")


async def upload_audio_files(
    client, channel_id: D.TextChannel, heading: str, files: list[str], texts: list[str]
):
    channel = client.get_channel(channel_id.id)
    print(channel_id.id)
    print(channel)
    if channel is not None:
        for pfile, text in zip(files, texts):
            loading_message = await channel.send("Loading tts hlaseni...")

            filename = Path(pfile).stem
            wav_audio = AudioSegment.from_wav(pfile)
            wav_audio.export(f"{filename}.mp3", format="mp3")

            file = D.File(f"{filename}.mp3")

            max_retries = 5
            retry_delay = 2
            for attempt in range(max_retries):
                print("attempt #", attempt)
                try:
                    msg = f"## {heading}\n{text}"
                    await loading_message.edit(content=msg, attachments=[file])
                    break  # If successful, exit the function

                except (HTTPException, Forbidden) as e:
                    if attempt < max_retries - 1:
                        print(
                            f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds..."
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        print(
                            f"Failed to send GIF after {max_retries} attempts. Error: {str(e)}"
                        )
                        await channel.send(
                            "Sorry, I couldn't send the GIF. Please try again later."
                        )

                except Exception as e:
                    print(f"Unexpected error: {str(e)}")
                    await channel.send(
                        "An unexpected error occurred. Please try again later."
                    )
                    return


@client.event
async def on_error(event, *args, **kwargs):
    logging.error(f"An error occurred in event {event}", exc_info=True)


def run_bot():
    client.run(BOT_TOKEN)


if __name__ == "__main__":
    try:
        run_bot()
    except Exception as e:
        logging.critical(f"Failed to start the bot: {e}")
