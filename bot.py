import discord
from discord.ext import tasks
from discord import app_commands
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

from playwright.async_api import async_playwright

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GUILD_ID = os.getenv("GUILD_ID")

USERNAME = "SkinSpotlights"
seen_ids = set()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


PROFILE_URL = f"https://x.com/{USERNAME}"


# -----------------------------
# FETCH TWEETS VIA PLAYWRIGHT
# -----------------------------
async def fetch_mythic_post():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(PROFILE_URL, timeout=60000)
            await page.wait_for_timeout(5000)  # allow JS to load

            content = await page.content()

            # Extract tweet blocks
            tweets = await page.query_selector_all("article")

            for t in tweets:
                text = (await t.inner_text()).lower()

                # FILTER: Mythic Shop only
                if "mythic" not in text or "shop" not in text:
                    continue

                # get link
                link = await t.query_selector("a[href*='/status/']")
                if not link:
                    continue

                href = await link.get_attribute("href")
                tweet_id = href.split("/")[-1]

                if tweet_id in seen_ids:
                    continue

                seen_ids.add(tweet_id)

                # images
                images = []
                imgs = await t.query_selector_all("img")

                for img in imgs:
                    src = await img.get_attribute("src")
                    if src and "twimg" in src:
                        images.append(src)

                await browser.close()

                return {
                    "id": tweet_id,
                    "url": f"https://x.com/{USERNAME}/status/{tweet_id}",
                    "images": images[:3]
                }

            await browser.close()
            return None

    except Exception as e:
        print("Playwright error:", e)
        return None


# -----------------------------
# /check COMMAND
# -----------------------------
@tree.command(name="check", description="Check Mythic Shop rotation (Playwright)")
async def check(interaction: discord.Interaction):

    await interaction.response.send_message("🔎 Checking Mythic Shop...")

    post = await fetch_mythic_post()

    if not post:
        await interaction.followup.send("❌ No Mythic Shop post found")
        return

    await interaction.followup.send(f"🚨 Mythic Shop Rotation detected!\n{post['url']}")

    for img in post["images"]:
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

        post = await fetch_mythic_post()

        if not post:
            return

        await channel.send("🚨 Mythic Shop Rotation detected!")
        await channel.send(post["url"])

        for img in post["images"]:
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
        await channel.send("✅ Playwright Mythic Bot online")

    scheduled_check.start()


client.run(DISCORD_TOKEN)
