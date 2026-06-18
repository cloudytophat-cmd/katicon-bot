import discord
from discord.ext import tasks
import os
import snscrape.modules.twitter as sntwitter
import requests
from PIL import Image
from io import BytesIO
import pytesseract
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

seen_tweets = set()

TARGET_ACCOUNT = "SkinSpotlights"


# -------------------------
# OCR CHECK
# -------------------------
def image_has_golden_katarina(image_url: str) -> bool:
    try:
        response = requests.get(image_url, timeout=10)
        img = Image.open(BytesIO(response.content))

        text = pytesseract.image_to_string(img).lower()

        print("OCR TEXT:", text)

        return "katarina" in text and "golden" in text

    except Exception as e:
        print("OCR error:", e)
        return False


# -------------------------
# FETCH X POSTS
# -------------------------
def fetch_latest_rotation():
    try:
        query = f"from:{TARGET_ACCOUNT} mythic shop"

        for tweet in sntwitter.TwitterSearchScraper(query).get_items():
            tweet_id = str(tweet.id)

            if tweet_id in seen_tweets:
                continue

            seen_tweets.add(tweet_id)

            text = tweet.content.lower()

            if "mythic shop" in text and "rotation" in text:
                images = []

                if tweet.media:
                    for m in tweet.media:
                        if hasattr(m, "fullUrl"):
                            images.append(m.fullUrl)

                return {
                    "id": tweet_id,
                    "text": tweet.content,
                    "images": images,
                    "url": tweet.url
                }

    except Exception as e:
        print("X fetch error:", e)

    return None


# -------------------------
# CHECK LOOP
# -------------------------
@tasks.loop(hours=1)
async def check_rotation():
    print("Checking X for Mythic Shop...")

    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found")
        return

    post = fetch_latest_rotation()

    if not post:
        print("No rotation found")
        return

    print("Rotation post found")

    # Check images for Golden Katarina
    match = False

    for img in post["images"]:
        if image_has_golden_katarina(img):
            match = True
            break

    if match:
        await channel.send("🚨 GOLDEN KATARINA DETECTED IN MYTHIC SHOP!")
        await channel.send(post["url"])
    else:
        print("Rotation found but no Golden Katarina")


# -------------------------
# SLASH COMMAND
# -------------------------
@client.event
async def on_message(message):
    if message.content == "/check":
        post = fetch_latest_rotation()

        if not post:
            await message.channel.send("❌ No rotation found")
            return

        await message.channel.send("Checking latest rotation...")

        match = False

        for img in post["images"]:
            if image_has_golden_katarina(img):
                match = True
                break

        if match:
            await message.channel.send("🚨 GOLDEN KATARINA DETECTED!")
        else:
            await message.channel.send("No Golden Katarina found.")


# -------------------------
# READY
# -------------------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Mythic Shop Bot (X-based) is online!")

    check_rotation.start()


client.run(TOKEN)
