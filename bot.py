import discord
from discord.ext import tasks
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

seen_ids = set()

USERNAME = "SkinSpotlights"


# -----------------------------
# X API FETCH FUNCTION
# -----------------------------
def fetch_latest_tweet():
    try:
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}"
        }

        # Get user ID
        user_url = f"https://api.twitter.com/2/users/by/username/{USERNAME}"
        user_resp = requests.get(user_url, headers=headers, timeout=10).json()

        if "data" not in user_resp:
            print("User fetch failed:", user_resp)
            return None

        user_id = user_resp["data"]["id"]

        # Get tweets
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
            if t["id"] in seen_ids:
                continue

            seen_ids.add(t["id"])

            text = t["text"].lower()

            if "mythic shop" in text and "rotation" in text:
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
# HOURLY CHECK LOOP
# -----------------------------
@tasks.loop(hours=1)
async def check_rotation():
    print("Checking X API...")

    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found")
        return

    tweet = fetch_latest_tweet()

    if not tweet:
        print("No rotation found")
        return

    await channel.send("🚨 Mythic Shop rotation detected!")
    await channel.send(tweet["url"])


# -----------------------------
# /check SLASH COMMAND
# -----------------------------
@tree.command(name="check", description="Check Mythic Shop rotation")
async def check(interaction: discord.Interaction):

    await interaction.response.defer()

    tweet = fetch_latest_tweet()

    if not tweet:
        await interaction.followup.send("❌ No rotation found")
        return

    await interaction.followup.send("🚨 Found latest Mythic Shop rotation!")
    await interaction.followup.send(tweet["url"])


# -----------------------------
# READY EVENT
# -----------------------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ X API Mythic Bot is online!")

    check_rotation.start()


client.run(DISCORD_TOKEN)
