import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

USERNAME = "SkinSpotlights"
KEYWORDS = ["mythic shop", "rotation"]


# -----------------------------
# PUBLIC FETCH (NO LOGIN)
# -----------------------------
def fetch_latest_posts():
    try:
        url = f"https://x.com/{USERNAME}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            print("HTTP error:", r.status_code)
            return None

        html = r.text.lower()

        return html

    except Exception as e:
        print("Fetch error:", e)
        return None


# -----------------------------
# DETECTION LOGIC
# -----------------------------
def detect_mythic_shop(html):
    if not html:
        return None

    if all(k in html for k in KEYWORDS):
        return True

    return False


# -----------------------------
# /check COMMAND
# -----------------------------
@tree.command(name="check", description="Check Mythic Shop updates (stable mode)")
async def check(interaction: discord.Interaction):

    await interaction.response.send_message("🔎 Checking Mythic Shop...")

    html = fetch_latest_posts()

    if detect_mythic_shop(html):
        await interaction.followup.send("🚨 Mythic Shop Rotation detected!")
    else:
        await interaction.followup.send("❌ No Mythic Shop rotation found")


# -----------------------------
# READY
# -----------------------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        await tree.sync()
    except Exception as e:
        print("Sync error:", e)

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Mythic Shop Bot (stable mode) online")


client.run(DISCORD_TOKEN)
