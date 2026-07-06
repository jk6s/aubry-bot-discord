import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime, timezone
import json
import re
import sqlite3
import time
import random
import shutil
import asyncio

#token = "MTUyM"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True




class MyBot(commands.Bot):
    async def setup_hook(self):
        guild = discord.Object(id=1523482176828473414)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"{len(synced)} commande(s) synchronisée(s)")
        for cmd in synced:
            print("-", cmd.name)

bot = MyBot(command_prefix="!", intents=intents)
cooldowns = {}


#------------------MESSAGES LOG CHANNEL-----------------------------

async def log_message_bot(bot, guild, message):
    channel = discord.utils.get(guild.text_channels, name="logs-bot")
    
    if channel:
        await channel.send(f"{message}")

async def log_message_tickets(bot, guild, message):
    channel = discord.utils.get(guild.text_channels, name="logs-tickets")
    
    if channel:
        await channel.send(f"{message}")
    


#------------------DEMARRAGE ET ARRETAGE DU BOT-----------------------------

@bot.event
async def on_ready():
    date = datetime.now(timezone.utc)

    for guild in bot.guilds:

        print(f"\n\n=======================\n{date}\n\n{bot.user} est connecté !\n|||||||||||||||||||||||\n-")
        await log_message_bot(bot, guild, f">>> ==========================\n{date}\n\n{bot.user} est connecté !\n==========================\n|||")

@bot.event
async def on_disconnect():
    for guild in bot.guilds:
        date = datetime.now(timezone.utc)

        print(f"--\n>>> {bot.user} est déconnecté\n--")
        await log_message_bot(bot, guild, f">>> {date}\n\n--\n>>> {bot.user} est déconnecté\n--")



#------------------COMMANDES DU BOT-----------------------------

@bot.command()
async def ping(ctx):
    await ctx.send("ntgrmslp")


@bot.tree.command(name="say", description="Envoie un message dans un salon")
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, salon: discord.TextChannel, message: str):
    message = message.replace("\\n", "\n")
    await salon.send(message)
    await interaction.response.send_message("Message envoyé ✅", ephemeral=True)

@say.error
async def say_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Tu n'as pas les permissions administrateur pour utiliser cette commande.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "❌ Tu n'as pas les permissions administrateur pour utiliser cette commande.",
                ephemeral=True
            )
    else:
        raise error
    

@bot.tree.command(name="ban", description="Enlève le ban de quelqu'un")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user_id: str):
    guild = interaction.guild

    try:
        user = await bot.fetch_user(int(user_id))
        date = datetime.now(timezone.utc)
        await guild.ban(user)

        await interaction.response.send_message(f"{user} a été débanni par {interaction.user}", ephemeral=True)
        await log_message_bot(bot, guild, f">>> 🔒BAN\n{date}\n{user} a été débanni par {interaction.user}")

    except ValueError:
        await interaction.response.send_message("❌ L'identifiant utilisateur est invalide.", ephemeral=True)

    except discord.NotFound:
        await interaction.response.send_message("❌ Cet utilisatuer n'est pas banni.", ephemeral=True)

@ban.error
async def unban_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    

@bot.tree.command(name="deban", description="Enlève le ban de quelqu'un")
@app_commands.checks.has_permissions(ban_members=True)
async def deban(interaction: discord.Interaction, user_id: str):
    guild = interaction.guild

    try:
        user = await bot.fetch_user(int(user_id))
        date = datetime.now(timezone.utc)
        await guild.unban(user)

        await interaction.response.send_message(f"{user} a été débanni par {interaction.user}", ephemeral=True)
        await log_message_bot(bot, guild, f">>> 🔓UNBAN\n{date}\n{user} a été débanni par {interaction.user}")

    except ValueError:
        await interaction.response.send_message("❌ L'identifiant utilisateur est invalide.", ephemeral=True)

    except discord.NotFound:
        await interaction.response.send_message("❌ Cet utilisatuer n'est pas banni.", ephemeral=True)

@deban.error
async def unban_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)




#bot.run(token) #(toujours a la fin)
bot.run(os.getenv("TOKEN"))
