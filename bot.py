import discord
from discord import app_commands
import os
import json
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

USERNAME = "SkinSpotlights"
SESSION_FILE = "storage_state.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# -----------------------------
# LOGIN SESSION SCRAPER
# -----------------------------
async def fetch_mythic_post():
    try:
        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=True)

            context_args = {}
            if os.path.exists(SESSION_FILE):
                context_args["storage_state"] = SESSION_FILE

            context = await browser.new_context(**context_args)
            page = await context.new_page()

            print("➡️ Opening X with session...")

            await page.goto(f"https://x.com/{USERNAME}", timeout=60000)
            await page.wait_for_timeout(8000)

            articles = await page.query_selector_all("article")

            print("Articles found:", len(articles))

            for article in articles:
                text = (await article.inner_text()).lower()

                if "mythic" not in text or "shop" not in text:
                    continue

                link = await article.query_selector("a[href*='/status/']")
                if not link:
                    continue

                href = await link.get_attribute("href")
                tweet_url = "https://x.com" + href

                images = []
                imgs = await article.query_selector_all("img")

                for img in imgs:
                    src = await img.get_attribute("src")
                    if src and "twimg" in src:
                        images.append(src)

                await browser.close()

                return {
                    "url": tweet_url,
                    "images": images[:3]
                }

            await browser.close()
            return None

    except Exception as e:
        print("Scraper error:", e)
        return None


# -----------------------------
# /check COMMAND
# -----------------------------
@tree.command(name="check", description="Check Mythic Shop rotation")
async def check(interaction: discord.Interaction):

    await interaction.response.send_message("🔎 Checking Mythic Shop...")

    post = await fetch_mythic_post()

    if not post:
        await interaction.followup.send("❌ No Mythic Shop rotation found")
        return

    await interaction.followup.send(f"🚨 Mythic Shop Rotation detected!\n{post['url']}")

    for img in post["images"]:
        await interaction.followup.send(img)


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

    print("Bot ready")


client.run(DISCORD_TOKEN)
