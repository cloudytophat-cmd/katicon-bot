import discord
from discord import app_commands
import os
from dotenv import load_dotenv

from playwright.async_api import async_playwright

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

USERNAME = "SkinSpotlights"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# -----------------------------
# FULL DEBUG SCRAPER
# -----------------------------
async def debug_fetch():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            page = await browser.new_page()

            print("➡️ Opening page...")
            await page.goto(f"https://x.com/{USERNAME}", timeout=60000)

            print("⏳ Waiting for render...")
            await page.wait_for_timeout(10000)

            print("📄 Page title:", await page.title())

            html = await page.content()

            print("\n===== HTML SNIPPET =====")
            print(html[:1200])

            articles = await page.query_selector_all("article")

            print("\n===== RESULTS =====")
            print("Articles found:", len(articles))

            # inspect first article if exists
            if articles:
                first_text = await articles[0].inner_text()
                print("\n===== FIRST TWEET TEXT =====")
                print(first_text[:500])

            await browser.close()

            return {
                "articles": len(articles)
            }

    except Exception as e:
        print("❌ Playwright error:", e)
        return None


# -----------------------------
# /check COMMAND
# -----------------------------
@tree.command(name="check", description="DEBUG X scrape test")
async def check(interaction: discord.Interaction):

    await interaction.response.send_message("🧪 Running debug scrape...")

    result = await debug_fetch()

    if not result:
        await interaction.followup.send("❌ Scrape failed (see logs)")
        return

    await interaction.followup.send(
        f"✅ Done\nArticles found: {result['articles']}"
    )


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

    print("Bot ready (debug mode)")


client.run(DISCORD_TOKEN)
