import os
import discord
from discord.ext import commands
import logging

from config import *
from utils.storage import load_stats
from commands.exempt import register_exempt
from commands.remove_exempt import register_remove_exempt
from scheduler import scheduler

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    await bot.process_commands(message)

# --- WEEKLY CHECK FUNCTION ---
async def weekly_mod_check():
    from utils.storage import save_stats
    logging.info("Running weekly mod check...")
    announce_channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
    if not announce_channel:
        return
    embed = discord.Embed(title="__**MOD CHECKS**__", color=discord.Color.blue())
    for guild in bot.guilds:
        mod_role = guild.get_role(MOD_ROLE_ID)
        trail_role = guild.get_role(TRAIL_MOD_ROLE_ID)
        head_role = guild.get_role(HEAD_MOD_ROLE_ID)

        # Trail Mods
        trail_text = ""
        if trail_role:
            for member in trail_role.members:
                user_id = str(member.id)
                stats = mod_stats.get(user_id, {"messages":0,"strikes":0,"exempt":False})
                status = "Exempted" if stats["exempt"] else "Promoted to @mod" if stats["messages"]>=MIN_MESSAGES else "Stayed/Not promoted"
                trail_text += f"<@{user_id}> - {status}\n"
                stats["messages"]=0
                mod_stats[user_id]=stats
            if trail_text:
                embed.add_field(name="Trail Mods", value=trail_text, inline=False)

        # Mods & Head Mods
        mod_text=""
        if mod_role:
            for member in mod_role.members:
                user_id=str(member.id)
                stats=mod_stats.get(user_id, {"messages":0,"strikes":0,"exempt":False})
                strike_limit=HEAD_STRIKE_LIMIT if head_role and head_role in member.roles else STRIKE_LIMIT

                if not stats["exempt"]:
                    if stats["messages"]<MIN_MESSAGES:
                        stats["strikes"]+=1
                        if stats["strikes"]>=strike_limit:
                            try:
                                await member.remove_roles(mod_role)
                                await member.send(f"You have been demoted for accumulating {stats['strikes']} strikes.")
                            except:
                                pass
                            action=f"Demoted (Strike {stats['strikes']})"
                        else:
                            action=f"Strike {stats['strikes']}"
                    else:
                        action="Stayed"
                else:
                    action="Exempted"
                mod_text+=f"<@{user_id}> - {action}\n"
                stats["messages"]=0
                mod_stats[user_id]=stats
            if mod_text:
                embed.add_field(name="Mods", value=mod_text, inline=False)

    save_stats()
    await announce_channel.send(embed=embed)

# --- ON READY ---
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    register_exempt(bot, mod_stats)
    register_remove_exempt(bot, mod_stats)
    bot.loop.create_task(scheduler())
    await bot.tree.sync()

# --- RUN BOT ---
bot.run(os.getenv("DISCORD_TOKEN"))
