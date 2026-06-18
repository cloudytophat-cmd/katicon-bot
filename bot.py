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
# FETCH + FILTER TWEETS PROPERLY
# -----------------------------
def fetch_mythic_tweet():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(PROFILE_URL, headers=headers, timeout=10)

        if r.status_code != 200:
            print("STATUS:", r.status_code)
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Find tweet blocks
        articles = soup.find_all("article")

        for article in articles:
            text = article.get_text(" ").lower()

            # -----------------------------
            # FILTER: only Mythic posts
            # -----------------------------
            if "mythic" not in text or "shop" not in text:
                continue

            # ignore pinned tweets (common keyword)
            if "pinned" in text:
                continue

            # find tweet link
            link = article.find("a", href=True)
            if not link:
                continue

            href = link["href"]
            if "/status/" not in href:
                continue

            tweet_id = href.split("/")[-1]

            if tweet_id in seen_ids:
                continue

            seen_ids.add(tweet_id)

            # find images
            images = []
            imgs = article.find_all("img")
            for img in imgs:
                src = img.get("src")
                if src and "twimg" in src:
                    images.append(src)

            return {
                "id": tweet_id,
                "url": f"https://x.com/{USERNAME}/status/{tweet_id}",
                "images": images
            }

        return None

    except Exception as e:
        print("Scrape error:", e)
        return None


# -----------------------------
# /check COMMAND (1 MESSAGE ONLY)
# -----------------------------
@tree.command(name="check", description="Check Mythic Shop rotation")
async def check(interaction: discord.Interaction):

    tweet = fetch_mythic_tweet()

    if not tweet:
        await interaction.response.send_message("❌ No Mythic Shop rotation found")
        return

    content = f"🚨 Mythic Shop Rotation detected!\n{tweet['url']}"

    await interaction.response.send_message(content)

    # send images in SAME command flow
    for img in tweet["images"][:3]:
        await interaction.followup.send(img)


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

        tweet = fetch_mythic_tweet()

        if not tweet:
            return

        await channel.send("🚨 Mythic Shop Rotation detected!")
        await channel.send(tweet["url"])

        for img in tweet["images"][:3]:
            await channel.send(img)


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
        await channel.send("✅ Mythic Bot (filtered) online")

    scheduled_check.start()


client.run(DISCORD_TOKEN)
