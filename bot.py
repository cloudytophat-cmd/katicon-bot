import discord
from discord.ext import tasks
from discord import app_commands
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

USERNAME = "SkinSpotlights"
seen_ids = set()

PROFILE_URL = f"https://x.com/{USERNAME}"


# -----------------------------
# FETCH LATEST TWEET VIA HTML
# -----------------------------
def fetch_latest_tweet():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(PROFILE_URL, headers=headers, timeout=10)

        print("STATUS:", r.status_code)

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Find tweet links
        tweets = soup.find_all("a", href=True)

        tweet_ids = []
        for t in tweets:
            if "/status/" in t["href"]:
                parts = t["href"].split("/")
                try:
                    tweet_id = parts[-1]
                    if tweet_id.isdigit():
                        tweet_ids.append(tweet_id)
                except:
                    continue

        if not tweet_ids:
            return None

        latest_id = tweet_ids[0]

        if latest_id in seen_ids:
            return None

        seen_ids.add(latest_id)

        tweet_url = f"https://x.com/{USERNAME}/status/{latest_id}"

        return {
            "id": latest_id,
            "url": tweet_url
        }

    except Exception as e:
        print("Scrape error:", e)
        return None


# -----------------------------
# /check COMMAND
# -----------------------------
@tree.command(name="check", description="Check latest Mythic Shop post")
async def check(interaction: discord.Interaction):

    await interaction.response.send_message("🔎 Checking latest post...")

    tweet = fetch_latest_tweet()

    if not tweet:
        await interaction.followup.send("❌ No post found (or blocked)")
        return

    await interaction.followup.send("📌 Latest post detected:")
    await interaction.followup.send(tweet["url"])


# -----------------------------
# SCHEDULED CHECK (2AM UTC)
# -----------------------------
@tasks.loop(minutes=1)
async def scheduled_check():
    now = datetime.now(timezone.utc)

    if now.hour == 2 and now.minute == 0:

        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            return

        tweet = fetch_latest_tweet()

        if not tweet:
            return

        await channel.send("🚨 Mythic Shop update detected!")
        await channel.send(tweet["url"])


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
        await channel.send("✅ No-API Mythic Bot online!")

    scheduled_check.start()


client.run(DISCORD_TOKEN)
