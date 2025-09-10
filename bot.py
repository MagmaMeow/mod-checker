import os
import discord
from discord.ext import commands
from discord import app_commands
import aioschedule
import asyncio
import logging
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import *
from utils.storage import load_stats, save_stats

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Load stats from JSON ---
mod_stats = load_stats()

# --- MESSAGE TRACKING ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if any(role.id in [MOD_ROLE_ID, TRAIL_MOD_ROLE_ID, HEAD_MOD_ROLE_ID] for role in message.author.roles):
        user_id = str(message.author.id)
        if user_id not in mod_stats:
            mod_stats[user_id] = {"messages": 0, "strikes": 0, "exempt": False}
        mod_stats[user_id]["messages"] += 1
        save_stats(mod_stats)

    await bot.process_commands(message)

# --- WEEKLY MOD CHECK ---
async def weekly_mod_check():
    logging.info("Running weekly mod check...")
    announce_channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
    if not announce_channel:
        logging.warning("Announcement channel not found!")
        return

    embed = discord.Embed(title="__**MOD CHECKS**__", color=discord.Color.blue())

    for guild in bot.guilds:
        mod_role = guild.get_role(MOD_ROLE_ID)
        trail_role = guild.get_role(TRAIL_MOD_ROLE_ID)
        head_role = guild.get_role(HEAD_MOD_ROLE_ID)

        # --- Trail Mods ---
        trail_text = ""
        if trail_role:
            for member in trail_role.members:
                user_id = str(member.id)
                stats = mod_stats.get(user_id, {"messages": 0, "strikes": 0, "exempt": False})
                status = "Exempted" if stats["exempt"] else "Promoted to @mod" if stats["messages"] >= MIN_MESSAGES else "Stayed/Not promoted"
                trail_text += f"<@{user_id}> - {status}\n"
                stats["messages"] = 0
                mod_stats[user_id] = stats
            if trail_text:
                embed.add_field(name="Trail Mods", value=trail_text, inline=False)

        # --- Mods & Head Mods ---
        mod_text = ""
        if mod_role:
            for member in mod_role.members:
                user_id = str(member.id)
                stats = mod_stats.get(user_id, {"messages": 0, "strikes": 0, "exempt": False})
                strike_limit = HEAD_STRIKE_LIMIT if head_role and head_role in member.roles else STRIKE_LIMIT

                if stats["exempt"]:
                    action = "Exempted"
                else:
                    if stats["messages"] < MIN_MESSAGES:
                        stats["strikes"] += 1
                        if stats["strikes"] >= strike_limit:
                            try:
                                await member.remove_roles(mod_role)
                                await member.send(f"You have been demoted for accumulating {stats['strikes']} strikes.")
                            except discord.Forbidden:
                                logging.warning(f"Cannot DM or remove roles for {member}")
                            action = f"Demoted (Strike {stats['strikes']})"
                        else:
                            action = f"Strike {stats['strikes']}"
                    else:
                        action = "Stayed"

                mod_text += f"<@{user_id}> - {action}\n"
                stats["messages"] = 0
                mod_stats[user_id] = stats

            if mod_text:
                embed.add_field(name="Mods", value=mod_text, inline=False)

    save_stats(mod_stats)
    await announce_channel.send(embed=embed)
    logging.info("Weekly mod check complete.")

# --- SCHEDULER ---
async def start_scheduler():
    aioschedule.every().saturday.at("01:00").do(weekly_mod_check)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)

# --- EXEMPT COMMAND ---
@app_commands.command(name="exempt", description="Exempt a user from mod checks temporarily")
@app_commands.describe(user="The user to exempt")
async def exempt(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id not in EXEMPT_USERS:
        await interaction.response.send_message("You are not allowed to use this command.", ephemeral=True)
        return

    user_id = str(user.id)
    if user_id not in mod_stats:
        mod_stats[user_id] = {"messages": 0, "strikes": 0, "exempt": True}
    else:
        mod_stats[user_id]["exempt"] = True

    save_stats(mod_stats)
    await interaction.response.send_message(f"<@{user_id}> is now exempt from this week's mod check.", ephemeral=False)

# --- REMOVE EXEMPT COMMAND ---
@app_commands.command(name="remove_exempt", description="Remove exemption from a user")
@app_commands.describe(user="The user to remove exemption from")
async def remove_exempt(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id not in EXEMPT_USERS:
        await interaction.response.send_message("You are not allowed to use this command.", ephemeral=True)
        return

    user_id = str(user.id)
    if user_id not in mod_stats:
        mod_stats[user_id] = {"messages": 0, "strikes": 0, "exempt": False}
    else:
        mod_stats[user_id]["exempt"] = False

    save_stats(mod_stats)
    await interaction.response.send_message(f"<@{user_id}> is no longer exempt from this week's mod check.", ephemeral=False)

# --- SIMPLE HTTP SERVER FOR RENDER FREE WEB SERVICE ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    port = int(os.environ.get("PORT", 10000))  # <- Render assigns this automatically
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- ON READY ---
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    bot.tree.add_command(exempt)
    bot.tree.add_command(remove_exempt)
    await bot.tree.sync()
    bot.loop.create_task(start_scheduler())

# --- RUN BOT ---
bot.run(os.getenv("DISCORD_TOKEN"))
