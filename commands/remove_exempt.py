import discord
from discord import app_commands
from config import EXEMPT_USERS
from utils.storage import save_stats

async def remove_exempt(interaction: discord.Interaction, user: discord.Member, mod_stats):
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

def register_remove_exempt(bot, mod_stats):
    @app_commands.command(name="remove_exempt", description="Remove exemption from a user")
    @app_commands.describe(user="The user to remove exemption from")
    async def cmd(interaction: discord.Interaction, user: discord.Member):
        await remove_exempt(interaction, user, mod_stats)
    bot.tree.add_command(cmd)
