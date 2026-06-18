import discord
from discord.ext import tasks
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

seen_ids = set()


# -------------------------
# REDDIT FETCHER
# -------------------------
def fetch_rotation_post():
    try:
        url = "https://www.reddit.com/r/leagueoflegends/new.json?limit=20"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        r = requests.get(url, headers=headers, timeout=10)

        print("Reddit status:", r.status_code)

        if r.status_code != 200:
            return None

        data = r.json()

        for post in data["data"]["children"]:
            p = post["data"]
            title = p["title"].lower()
            post_id = p["id"]

            if post_id in seen_ids:
                continue

            if "mythic shop" in title and "rotation" in title:
                seen_ids.add(post_id)

                return {
                    "id": post_id,
                    "title": p["title"],
                    "image": p.get("url_overridden_by_dest"),
                    "url": "https://reddit.com" + p["permalink"]
                }

    except Exception as e:
        print("Reddit error:", e)

    return None


# -------------------------
# HOURLY CHECK
# -------------------------
@tasks.loop(hours=1)
async def check_rotation():
    print("Checking for Mythic Shop updates...")

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found")
        return

    result = fetch_rotation_post()

    if result:
        await channel.send("🚨 Mythic Shop Rotation detected!")

        if result.get("image"):
            await channel.send(result["image"])

        await channel.send(result["url"])
    else:
        print("No update found")


# -------------------------
# SLASH COMMAND (/check)
# -------------------------
@bot.slash_command(name="check", description="Manually check Mythic Shop updates")
async def check(ctx):
    await ctx.respond("Checking Mythic Shop...")

    result = fetch_rotation_post()

    if not result:
        await ctx.followup.send("❌ No update found.")
        return

    await ctx.followup.send("🚨 Mythic Shop Rotation detected!")

    if result.get("image"):
        await ctx.followup.send(result["image"])

    await ctx.followup.send(result["url"])


# -------------------------
# ON READY (IMPORTANT FIX HERE)
# -------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online!")

    # IMPORTANT: force slash command sync
    await bot.sync_commands()

    check_rotation.start()


# -------------------------
# RUN BOT
# -------------------------
bot.run(TOKEN)
