import discord
from discord.ext import tasks
from discord import app_commands
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

USERNAME = "SkinSpotlights"


# -----------------------------
# DEBUG: RAW X API OUTPUT
# -----------------------------
def fetch_debug_data():
    try:
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

        # Step 1: get user info
        user_url = f"https://api.twitter.com/2/users/by/username/{USERNAME}"
        user_resp = requests.get(user_url, headers=headers, timeout=10).json()

        print("\n===== USER RESPONSE =====")
        print(user_resp)

        if "data" not in user_resp:
            return "NO_USER_DATA"

        user_id = user_resp["data"]["id"]

        # Step 2: get tweets
        tweet_url = (
            f"https://api.twitter.com/2/users/{user_id}/tweets"
            f"?max_results=5"
            f"&tweet.fields=created_at,text"
            f"&expansions=attachments.media_keys"
            f"&media.fields=url"
        )

        tweet_resp = requests.get(tweet_url, headers=headers, timeout=10).json()

        print("\n===== TWEET RESPONSE =====")
        print(tweet_resp)

        return "DONE"

    except Exception as e:
        print("ERROR:", e)
        return "ERROR"


# -----------------------------
# /check COMMAND (DEBUG VERSION)
# -----------------------------
@tree.command(name="check", description="DEBUG: Show raw X API response")
async def check(interaction: discord.Interaction):

    await interaction.response.defer()

    result = fetch_debug_data()

    await interaction.followup.send(f"🧪 Debug finished: `{result}`")


# -----------------------------
# READY
# -----------------------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            await tree.sync(guild=guild)
        else:
            await tree.sync()
    except Exception as e:
        print("Sync error:", e)

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🧪 DEBUG BOT ONLINE - X API inspection mode")

    print("Bot is ready for debugging.")


client.run(DISCORD_TOKEN)
