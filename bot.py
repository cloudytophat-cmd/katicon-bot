import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

USERNAME = "SkinSpotlights"


# -----------------------------
# SAFE DEBUG FUNCTION
# -----------------------------
def fetch_debug_data():
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    user_url = f"https://api.twitter.com/2/users/by/username/{USERNAME}"
    user_resp = requests.get(user_url, headers=headers, timeout=10).json()

    print("\n===== USER RESPONSE =====")
    print(user_resp)

    if "data" not in user_resp:
        return None, None

    user_id = user_resp["data"]["id"]

    tweet_url = f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=5"

    tweet_resp = requests.get(tweet_url, headers=headers, timeout=10).json()

    print("\n===== TWEET RESPONSE =====")
    print(tweet_resp)

    return user_resp, tweet_resp


# -----------------------------
# /check COMMAND (FIXED SAFE FLOW)
# -----------------------------
@tree.command(name="check", description="Debug X API")
async def check(interaction: discord.Interaction):

    # STEP 1: respond instantly (prevents 10062 error)
    await interaction.response.send_message("🧪 Checking X API...")

    # STEP 2: do work AFTER response
    user_resp, tweet_resp = fetch_debug_data()

    if not user_resp or not tweet_resp:
        await interaction.followup.send("❌ No data found from X API")
        return

    await interaction.followup.send("✅ Debug complete. Check Railway logs.")


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

    print("Bot ready.")


client.run(DISCORD_TOKEN)
