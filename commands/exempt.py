import discord
from discord import app_commands
from config import EXEMPT_USERS
from utils.storage import save_stats

async def exempt(interaction: discord.Interaction, user: discord.Member, mod_stats):
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

# Create app command wrapper
def register_exempt(bot, mod_stats):
    @app_commands.command(name="exempt", description="Exempt a user from mod checks temporarily")
    @app_commands.describe(user="The user to exempt")
    async def cmd(interaction: discord.Interaction, user: discord.Member):
        await exempt(interaction, user, mod_stats)
    bot.tree.add_command(cmd)
