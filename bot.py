import discord
from discord.ext import tasks
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)

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
    print("Checking Mythic Shop updates...")

    channel = client.get_channel(CHANNEL_ID)
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
# SLASH COMMAND
# -------------------------
@tree.command(name="check", description="Manually check Mythic Shop updates")
async def check(interaction: discord.Interaction):
    await interaction.response.defer()

    result = fetch_rotation_post()

    if not result:
        await interaction.followup.send("❌ No update found.")
        return

    await interaction.followup.send("🚨 Mythic Shop Rotation detected!")

    if result.get("image"):
        await interaction.followup.send(result["image"])

    await interaction.followup.send(result["url"])


# -------------------------
# READY EVENT
# -------------------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    await tree.sync()

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot is online!")

    check_rotation.start()


client.run(TOKEN)
