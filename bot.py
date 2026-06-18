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

seen_ids = set()

USERNAME = "SkinSpotlights"


# -----------------------------
# FETCH LATEST VALID TWEET
# -----------------------------
def fetch_latest_tweet():
    try:
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

        user_url = f"https://api.twitter.com/2/users/by/username/{USERNAME}"
        user_resp = requests.get(user_url, headers=headers, timeout=10).json()

        if "data" not in user_resp:
            print("User fetch failed:", user_resp)
            return None

        user_id = user_resp["data"]["id"]

        tweet_url = (
            f"https://api.twitter.com/2/users/{user_id}/tweets"
            f"?max_results=10"
            f"&expansions=attachments.media_keys"
            f"&media.fields=url"
        )

        tweet_resp = requests.get(tweet_url, headers=headers, timeout=10).json()

        if "data" not in tweet_resp:
            print("Tweet fetch failed:", tweet_resp)
            return None

        tweets = tweet_resp["data"]
        includes = tweet_resp.get("includes", {})

        media_map = {}
        for m in includes.get("media", []):
            media_map[m["media_key"]] = m.get("url")

        for t in tweets:
            text = t.get("text", "").lower()

            # -----------------------------
            # FIXED DETECTION LOGIC
            # -----------------------------
            if "mythic" not in text or "shop" not in text:
                continue

            if t["id"] in seen_ids:
                continue

            seen_ids.add(t["id"])

            images = []
            attachments = t.get("attachments", {})

            for key in attachments.get("media_keys", []):
                if key in media_map:
                    images.append(media_map[key])

            return {
                "id": t["id"],
                "text": t["text"],
                "images": images,
                "url": f"https://x.com/{USERNAME}/status/{t['id']}"
            }

    except Exception as e:
        print("X API error:", e)

    return None


# -----------------------------
# SCHEDULED 2AM UTC CHECK
# -----------------------------
@tasks.loop(minutes=1)
async def scheduled_check():
    now = datetime.now(timezone.utc)

    if now.hour == 2 and now.minute == 0:
        print("Running scheduled 2AM check...")

        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            return

        tweet = fetch_latest_tweet()

        if not tweet:
            print("No Mythic Shop update found")
            return

        await channel.send("🚨 Mythic Shop Rotation detected!")
        await channel.send(tweet["url"])

        for img in tweet["images"]:
            await channel.send(img)


# -----------------------------
# /check COMMAND
# -----------------------------
@tree.command(name="check", description="Check Mythic Shop rotation manually")
async def check(interaction: discord.Interaction):

    await interaction.response.defer()

    tweet = fetch_latest_tweet()

    if not tweet:
        await interaction.followup.send("❌ No Mythic Shop rotation found")
        return

    await interaction.followup.send("✅ Mythic Shop Rotation found!")
    await interaction.followup.send(tweet["url"])

    for img in tweet["images"]:
        await interaction.followup.send(img)


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
            print("Guild slash commands synced.")
        else:
            synced = await tree.sync()
            print(f"Global sync complete: {len(synced)} commands")

    except Exception as e:
        print("Sync error:", e)

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ X API Mythic Bot is online!")

    scheduled_check.start()


client.run(DISCORD_TOKEN)
