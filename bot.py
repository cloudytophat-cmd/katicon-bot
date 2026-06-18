import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # optional

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

USERNAME = "SkinSpotlights"
KEYWORDS = ["mythic shop", "rotation"]


# -----------------------------
# FETCH X HTML (PUBLIC)
# -----------------------------
def fetch_latest_posts():
    try:
        url = f"https://x.com/{USERNAME}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=15)

        print("STATUS:", r.status_code)
        print("HTML SIZE:", len(r.text))

        if r.status_code != 200:
            return None

        return r.text.lower()

    except Exception as e:
        print("Fetch error:", e)
        return None


# -----------------------------
# DETECTION LOGIC
# -----------------------------
def detect_mythic_shop(html):
    if not html:
        return False

    return all(k in html for k in KEYWORDS)


# -----------------------------
# /check COMMAND (FIXED)
# -----------------------------
@tree.command(name="check", description="Check Mythic Shop updates")
async def check(interaction: discord.Interaction):

    # IMPORTANT: prevents "outdated command" / timeout issues
    await interaction.response.defer()

    html = fetch_latest_posts()

    if detect_mythic_shop(html):
        await interaction.followup.send("🚨 Mythic Shop Rotation detected!")
    else:
        await interaction.followup.send("❌ No Mythic Shop rotation found")


# -----------------------------
# READY EVENT
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

    print("Bot is ready")


client.run(DISCORD_TOKEN)
