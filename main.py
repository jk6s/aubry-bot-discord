
import discord
from discord.ext import commands
import os
from datetime import datetime, timezone
import json
import re
import sqlite3
import time
import random
import shutil
import asyncio

LINK_REGEX = re.compile(r"(https?://|www\.|discord\.gg/|discord\.com/invite/)")

#token = ""

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
cooldowns = {}
DB_PATH = "data/levels.db"
if not os.path.exists("data"):
    os.makedirs("data")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS levels (
        user_id TEXT PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()



#------------------MESSAGES LOG CHANNEL-----------------------------

async def log_message_bot(bot, guild, message):
    channel = discord.utils.get(guild.text_channels, name="logs-bot")
    
    if channel:
        await channel.send(f"{message}")

async def log_message_JL(bot, guild, message):
    channel = discord.utils.get(guild.text_channels, name="logs-join-leave-member")
    
    if channel:
        await channel.send(f"{message}")

async def log_message_voc(bot, guild, message):
    channel = discord.utils.get(guild.text_channels, name="logs-voc")
    
    if channel:
        await channel.send(f"{message}")

async def log_message_tickets(bot, guild, message):
    channel = discord.utils.get(guild.text_channels, name="logs-tickets")
    
    if channel:
        await channel.send(f"{message}")
    



#------------------DEMARRAGE ET ARRETAGE DU BOT-----------------------------

@bot.event
async def on_ready():
    for guild in bot.guilds:
        date = datetime.now(timezone.utc)

        bot.add_view(TicketView())

        init_db()
        bot.loop.create_task(auto_backup())
        print(f"\n\n=======================\n{date}\n\n{bot.user} est connecté !\n+Base SQLite initialisée\n|||||||||||||||||||||||\n-")
        await log_message_bot(bot,guild,f">>> ==========================\n{date}\n\n{bot.user} est connecté !\n+Base SQLite initialisée\n==========================\n|||")

@bot.event
async def on_disconnect():
    for guild in bot.guilds:
        date = datetime.now(timezone.utc)

        print(f"--\n>>> {bot.user} est déconnecté\n--")
        await log_message_bot(bot, guild, f">>> {date}\n\n--\n>>> {bot.user} est déconnecté\n--")



#------------------COMMANDES DU BOT-----------------------------!ping, !nonpourquoitudiscaslp, !datejoin @membre, !ouvrirunticket etc...

@bot.command()
async def ping(ctx):
    await ctx.send("ntgrmslp")

@bot.command()
async def ntmlebot(ctx):
    await ctx.send("Inutile d’être agressif, je peux t’aider si tu veux poser une vraie question. Je suis là pour aider, pas pour me disputer. Pas besoin d’insultes. Reformule calmement et je te réponds.")

@bot.command()
async def ntmmmeaubry(ctx):
    await ctx.send("Inutile d’être agressif, je peux t’aider si tu veux poser une vraie question. Je suis là pour aider, pas pour me disputer. Pas besoin d’insultes. Reformule calmement et je te réponds.")

@bot.command()
async def ntmaubry(ctx):
    await ctx.send("Inutile d’être agressif, je peux t’aider si tu veux poser une vraie question. Je suis là pour aider, pas pour me disputer. Pas besoin d’insultes. Reformule calmement et je te réponds.")

@bot.command()
async def soleilterre(ctx):
    await ctx.send("Il doit yen avoir environ 12")

@bot.command()
async def nonpourquoitudiscaslp(ctx):
    await ctx.send("fdp")

@bot.command()
async def depuis(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    datejoin = member.joined_at.strftime("%d/%m/%Y à %H:%M")
    await ctx.send(f"{member.display_name} a rejoint le serveur le : {datejoin}")

@bot.command()
@commands.has_permissions(administrator=True)
async def ouvrirunticket(ctx):
    await ctx.send(
        "🎟️ **Support Tickets**\n\nClique sur le bouton pour ouvrir un ticket.\n\n",
        view=TicketView()
    )

@bot.command()
async def closeticket(ctx):

    channel = ctx.channel
    guild = ctx.guild
    channel_name = channel.name

    # Vérifie que la commande est utilisée dans un ticket
    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("❌ Cette commande ne peut être utilisée que dans un ticket.")
        return

    role_tickets = discord.utils.get(ctx.guild.roles, name="<tickets>")

    has_ticket_role = (
        role_tickets is not None
        and role_tickets in ctx.author.roles
    )

    if (
        not has_ticket_role
        and not ctx.author.guild_permissions.manage_channels
    ):
        await ctx.send("❌ Tu n'as pas la permission de fermer ce ticket.")
        return

    await ctx.send("🔒 Fermeture du ticket...")

    messages = []

    async for msg in channel.history(limit=200, oldest_first=True):
        messages.append({
            "author": str(msg.author),
            "content": msg.content,
            "time": str(msg.created_at)
        })

    now = datetime.now(timezone.utc)
    formatted_date = now.strftime("%d.%m.%y_%Hh%M")

    data = {
        "channel_name": channel.name,
        "closed_by": str(ctx.author),
        "closed_at": str(datetime.now(timezone.utc)),
        "messages": messages
    }
        
    if not os.path.exists("tickets_backup"):
        os.makedirs("tickets_backup")

    filename = f"{channel.name}_{formatted_date}.json"
    file_path = os.path.join("tickets_backup", filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"--> {datetime.now(timezone.utc)} Ticket fermé : {channel_name} par {ctx.author}")

    await log_message_tickets(
        bot,
        guild, 
        f">>> ---__CLOSE__---\n{datetime.now(timezone.utc)}\n\nTicket fermé : {channel_name}\nPar {ctx.author}"
    )

    log_channel = discord.utils.get(guild.text_channels, name="backup-tickets")

    if log_channel is None:
        print("Salon de logs introuvable.")
    else:
        await log_channel.send(
            content=f"📁 Backup du ticket **{channel.name}** fermé par {ctx.author.mention}",
            file=discord.File(file_path)
        )

    await channel.delete()    

@bot.command()
async def rank(ctx, member: discord.Member = None):

    member = member or ctx.author

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT xp, level FROM levels WHERE user_id = ?",
        (str(member.id),)
    )

    result = c.fetchone()
    conn.close()

    if not result:
        await ctx.send("❌ Aucun niveau trouvé.")
        return

    xp, level = result

    await ctx.send(
        f"📊 {member.display_name}\n"
        f"⭐ Niveau : {level}\n"
        f"📈 XP : {xp}"
    )

@bot.command()
async def leaderboard(ctx):

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT user_id, level, xp
        FROM levels
        ORDER BY level DESC, xp DESC
        LIMIT 10
    """)

    data = c.fetchall()
    conn.close()

    embed = discord.Embed(
        title="🏆 Leaderboard",
        color=discord.Color.gold()
    )

    for i, (user_id, level, xp) in enumerate(data, start=1):
        user = await bot.fetch_user(int(user_id))

        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"Niveau {level} - XP {xp}",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command()
async def givexp(ctx, member: discord.Member = None, amount: int = None):

    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande")
        return

    if amount is None:
        await ctx.send("❌ Tu dois préciser une quantité d'XP.")
        return

    member = member or ctx.author
    user_id = str(member.id)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    if result is None:
        xp = amount
        level = 1
        c.execute(
            "INSERT INTO levels (user_id, xp, level) VALUES (?, ?, ?)",
            (user_id, xp, level)
        )
    else:
        xp, level = result
        xp += amount

        c.execute(
            "UPDATE levels SET xp = ? WHERE user_id = ?",
            (xp, user_id)
        )

    conn.commit()
    conn.close()

    await ctx.send(
        f"✅ {amount} XP ajouté à {member.mention}"
    )

@bot.command()
async def setlevel(ctx, member: discord.Member = None, level: int = None):

    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande")
        return

    if level is None:
        await ctx.send("❌ Tu dois préciser un niveau.")
        return

    member = member or ctx.author
    user_id = str(member.id)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT xp FROM levels WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    if result is None:
        xp = 0
        c.execute(
            "INSERT INTO levels (user_id, xp, level) VALUES (?, ?, ?)",
            (user_id, xp, level)
        )
    else:
        xp = 0
        c.execute(
            "UPDATE levels SET xp = ?, level = ? WHERE user_id = ?",
            (xp, level, user_id)
        )

    conn.commit()
    conn.close()

    await ctx.send(
        f"⭐ {member.mention} est maintenant niveau {level}"
    )



#------------------ANTILINK-----------------------------

LINK_REGEX = re.compile(r"(https?://|www\.|discord\.gg/|discord\.com/invite/)")

LOG_CHANNEL_ID = 1523109860974002258

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return

    role_tickets = discord.utils.get(message.guild.roles, name="<tickets>")

    has_ticket_role = (
        role_tickets is not None
        and role_tickets in message.author.roles
    )

    if has_ticket_role and message.channel.name.startswith("ticket-"):
        await bot.process_commands(message)
        return

    if LINK_REGEX.search(message.content):

        contenu = message.content
        salon = message.channel

        await message.delete()

        log_channel = message.guild.get_channel(LOG_CHANNEL_ID)

        if log_channel:
            embed = discord.Embed(
                title="🚫 Lien bloqué",
                color=discord.Color.red()
            )

            embed.add_field(
                name="👤 Auteur",
                value=message.author.mention,
                inline=False
            )

            embed.add_field(
                name="📍 Salon",
                value=salon.mention,
                inline=False
            )

            embed.add_field(
                name="🔗 Message",
                value=f"```{contenu}```",
                inline=False
            )

            embed.set_thumbnail(url=message.author.display_avatar.url)

            await log_channel.send(embed=embed)

        await message.channel.send(
            f"{message.author.mention} ❌ Les liens sont interdits sur ce serveur.",
            delete_after=5
        )

        return

    await bot.process_commands(message)



#------------------JOIN ET LEAVE D'UN MEMBRE-----------------------------

@bot.event
async def on_member_join(member):
    guild = member.guild
    
    channel = discord.utils.get(member.guild.text_channels, name="🛬bienvenue")
    role = discord.utils.get(member.guild.roles, name="Membre")

    if role:
        await member.add_roles(role)
    
    embed = discord.Embed(
    title=f"🔥 MAIS NAN UN NOUVEAU MEMBRE ! 🔥",
    description=(
        f"Bienvenue {member.mention} sur le serveur !\n*Nous sommes maintenant {member.guild.member_count} membres 🎉*"),

    color=discord.Color.gold())

    embed.set_thumbnail(url=member.display_avatar.url)

    if channel:

        date = datetime.now(timezone.utc)

        print(f"--> {date}, {member} a rejoint le serveur, {member.guild.member_count} membres")
        await log_message_JL(
            bot,
            guild, 
            f">>> ------------------------------------\n{date}\n\n{member} a rejoint le serveur\n{member.guild.member_count} membres\n------------------------------------\n|")
        await channel.send(embed=embed)

#ban/deban/kick

@bot.event
async def on_member_ban(guild, user):
    salon = discord.utils.get(guild.text_channels, name="logs-join-leave-member")
    date = datetime.now(timezone.utc)

    if user.joined_at is None:
        return
    
    duration = datetime.now(timezone.utc) - user.joined_at

    datejoin = user.joined_at
    date = datetime.now(timezone.utc)

    days = duration.days
    hours = duration.seconds //3600
    minutes = (duration.seconds // 60) % 60
    seconds = duration.seconds - (((duration.seconds // 60) % 60) * 60)
    totalseconds = duration.seconds

    if not salon:
        return
    
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == user.id:
            print(f"--> {date}\n\n{user} s'est fait ban par {entry.user}\nRaison : {entry.reason or 'Aucune raison'}\nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s\n{totalseconds}s au total\n{user.guild.member_count} membres à présent\n")
            await log_message_JL(bot, guild, f">>> --------------------------\n{date}\n\n{user} ({user.mention}) s'est fait ban par {entry.user}\nRaison : {entry.reason or 'Aucune raison'}\nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s\n{totalseconds}s au total\n{user.guild.member_count} membres à présent\n--------------------------")
            return
        
@bot.event
async def on_member_unban(guild, user):
    salon = discord.utils.get(guild.text_channels, name="logs-join-leave-member")
    date = datetime.now(timezone.utc)

    if user.joined_at is None:
        return

    duration = datetime.now(timezone.utc) - user.joined_at

    date = datetime.now(timezone.utc)


    if not salon:
        return
    
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == user.id:

            print(f"--> {date}\n\n{user} s'est fait deban par {entry.user}\n\n{user.guild.member_count} membres à présent\n")
            await log_message_JL(f">>> --------------------------\n{date}\n\n**{user}** ({user.mention}) a été débanni.")

@bot.event
async def on_member_remove(member):
    date = datetime.now(timezone.utc)

    if member.joined_at is None:
        return

    duration = datetime.now(timezone.utc) - member.joined_at

    datejoin = member.joined_at
    date = datetime.now(timezone.utc)

    days = duration.days
    hours = duration.seconds //3600
    minutes = (duration.seconds // 60) % 60
    seconds = duration.seconds - (((duration.seconds // 60) % 60) * 60)
    totalseconds = duration.seconds


    await asyncio.sleep(1)  # Laisse le temps aux logs d'audit de se mettre à jour

    #ban
    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == member.id:
            return  

    #kick
    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target.id == member.id:
            salon = member.guild.get_channel(1523023647781027921)
            if salon:
                print(f"--> {date}\n\n{member} s'est fait kick par {entry.user}\nRaison : {entry.reason or 'Aucune raison'}\nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s\n{totalseconds}s au total\n{member.guild.member_count} membres à présent\n")
                await log_message_JL(bot, guild, f">>> --------------------------\n{date}\n\n{member} ({member.mention}) s'est fait kick par {entry.user}\nRaison : {entry.reason or 'Aucune raison'}\nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s\n{totalseconds}s au total\n{member.guild.member_count} membres à présent\n--------------------------")

            return

    #juste leave
    salon = member.guild.get_channel(1523023647781027921)
    guild = member.guild
    if salon:
        print(f"--> {date}\n\n{member} a quitte le serveur \nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s  ({totalseconds}s au total), {member.guild.member_count} membres")
        await log_message_JL(
            bot,
            guild, 
            f">>> --------------------------\n{date}\n\n{member} ({member.mention}) a quitte le serveur\nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s\n{totalseconds}s au total\n{member.guild.member_count} membres à présent\n--------------------------")



#------------------SALONS VOCAUX TEMPORAIRES-----------------------------

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    create_channel = discord.utils.get(guild.voice_channels, name="Créez votre salon")
    category = discord.utils.get(guild.categories, name="🎙️ Vocal")

    if after.channel == create_channel:

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True),
            member: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_voice_channel(
            name=f"🔊 vocal-{member.name}",
            category=category,  
            overwrites=overwrites
        )

        await member.move_to(channel)
        
    if before.channel != after.channel:
        if after.channel and after.channel != create_channel:
            print(f"--> {datetime.now(timezone.utc)} {member} a rejoint : {after.channel.name}")
            await log_message_voc(
                bot,
                guild, 
                f">>> __________________________\n{datetime.now(timezone.utc)}\n\n{member} a rejoint : {after.channel.mention}")
        
    if before.channel and before.channel != after.channel:
        print(f"\n--> {datetime.now(timezone.utc)} {member} a quitté : {before.channel.name}")
        await log_message_voc(
            bot,
            guild,
            f">>> __________________________\n{datetime.now(timezone.utc)}\n\n{member} a quitté : {before.channel.mention}"
        )
        
    if before.channel and before.channel.name.startswith("🔊 vocal-"):
        if len(before.channel.members) == 0:
            try:
                await before.channel.delete()
                print(f"supprimé : {before.channel.name}")

                await log_message_voc(
                    bot,
                    guild,
                    f">>> __________________________\n"
                    f"{datetime.now(timezone.utc)}\n\n"
                    f"Supprimé : {before.channel.name}"
                )
            except discord.NotFound:
                pass
    


#------------------TICKETS-----------------------------

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎟️ Ouvrir un ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        member = interaction.user

        await interaction.response.defer(ephemeral=True)

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing:
            await interaction.followup.send("❌ Tu as déjà un ticket.", ephemeral=True)
            return

        category = discord.utils.get(guild.categories, name="TICKETS")
        role_tickets = discord.utils.get(guild.roles, name="<tickets>")
        

        if category is None:
            await interaction.followup.send("❌ Catégorie introuvable.", ephemeral=True)
            return

        if role_tickets is None:
            await interaction.followup.send("❌ Rôle introuvable.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            role_tickets: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{member.name}",
            category=category,
            overwrites=overwrites
        )

        print(f"--> {datetime.now(timezone.utc)} Ticket créé : {channel.name} par {member} | ID: {channel.id}")

        await log_message_tickets(
            bot,
            guild, 
            f">>> ===__OPEN__===\n{datetime.now(timezone.utc)}\n\nTicket créé : {channel.name}\nPar {member}\nSalon : {channel.mention}\nID: {channel.id}"
        )

        await interaction.followup.send(
            f"✅ Ticket créé : {channel.mention}",
            ephemeral=True
        )

        embed = discord.Embed(
            title=f"🎟️ TICKET par {member.display_name}",
            description=(f"{member.mention} décris ta demande :\n\n• Explique clairement\n• Ajoute des screenshots si besoin\n• Pas de spam\n• Respect du staff"),
            color=discord.Color.purple()
        )

        await channel.send(
            content=role_tickets.mention,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        await channel.send(
            embed=embed,
            view=CloseTicketView()
        )

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        channel = interaction.channel
        guild = channel.guild
        channel_name = channel.name
        role_tickets = discord.utils.get(interaction.guild.roles, name="<tickets>")

        if (role_tickets not in interaction.user.roles and not interaction.user.guild_permissions.manage_channels):
            await interaction.response.send_message("❌ Tu n'as pas la permission de fermer ce ticket.",ephemeral=True)
            return
        
        await interaction.response.send_message("🔒 Fermeture du ticket...", ephemeral=True)
        
        messages = []

        async for msg in channel.history(limit=200, oldest_first=True):
            messages.append({
                "author": str(msg.author),
                "content": msg.content,
                "time": str(msg.created_at)
            })

        now = datetime.now(timezone.utc)
        formatted_date = now.strftime("%d.%m.%y_%Hh%M")

        data = {
            "channel_name": channel.name,
            "closed_by": str(interaction.user),
            "closed_at": str(datetime.now(timezone.utc)),
            "messages": messages
        }
        
        if not os.path.exists("tickets_backup"):
            os.makedirs("tickets_backup")

        filename = f"{channel.name}_{formatted_date}.json"
        file_path = os.path.join("tickets_backup", filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"--> {datetime.now(timezone.utc)} Ticket fermé : {channel_name} par {interaction.user}")

        await log_message_tickets(
            bot,
            guild, 
            f">>> ---__CLOSE__---\n{datetime.now(timezone.utc)}\n\nTicket fermé : {channel_name}\nPar {interaction.user}"
        )

        log_channel = discord.utils.get(guild.text_channels, name="backup-tickets")

        if log_channel is None:
            print("Salon de logs introuvable.")
        else:
            await log_channel.send(
                content=f"📁 Backup du ticket **{channel.name}** fermé par {interaction.user.mention}",
                file=discord.File(file_path)
            )

        await channel.delete()



    @discord.ui.button(label="➕ Ajouter un membre", style=discord.ButtonStyle.secondary)
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        member = interaction.user

        role = discord.utils.get(guild.roles, name="<tickets>")

        if role not in member.roles:
            await interaction.response.send_message(
                "❌ Tu n'as pas la permission d'ajouter des membres.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "👤 Mentionne la personne à ajouter ",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=120)
        except:
            await interaction.followup.send("❌ Temps écoulé.", ephemeral=True)
            return

        await msg.delete()

        if not msg.mentions:
            await interaction.followup.send("❌ Aucun utilisateur détecté.", ephemeral=True)
            return

        user = msg.mentions[0]
        channel = interaction.channel

        await channel.set_permissions(user, view_channel=True, send_messages=True)

        await interaction.followup.send(
            f"✅ Utilisateur ajouté.",
            ephemeral=True
        )



#------------------NIVEAUX-----------------------------

def backup_db():
    if not os.path.exists("backups"):
        os.makedirs("backups")

    date = datetime.now().strftime("%d-%m-%Y_%Hh%M")

    shutil.copy(
        DB_PATH,
        f"backups/levels_{date}.db"
    )

async def auto_backup():
    while True:
        backup_db()
        await asyncio.sleep(3600)  

def add_xp(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    xp_gain = random.randint(9, 12)
    leveled_up = False

    if result is None:
        xp = xp_gain
        level = 1

        c.execute(
            "INSERT INTO levels (user_id, xp, level) VALUES (?, ?, ?)",
            (user_id, xp, level)
        )

    else:
        xp, level = result
        xp += xp_gain

        xp_needed = level * 100

        if xp >= xp_needed:
            xp -= xp_needed
            level += 1
            leveled_up = True

        c.execute(
            "UPDATE levels SET xp = ?, level = ? WHERE user_id = ?",
            (xp, level, user_id)
        )

    conn.commit()
    conn.close()

    return xp, level, leveled_up

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    now = time.time()

    # anti spam XP
    if user_id in cooldowns:
        if now - cooldowns[user_id] < 5:
            await bot.process_commands(message)
            return

    cooldowns[user_id] = now

    xp, level, leveled_up = add_xp(user_id)

    if leveled_up:
        
        niveaux_channel = 1486065141966438462
        channel = bot.get_channel(niveaux_channel)

        if channel:
            embed = discord.Embed(
                title="🎉 Level Up !",
                description=(
                    f"👤 {message.author.mention}\n"
                    f"⭐ Nouveau niveau : **{level}**"
                ),
                color=discord.Color.gold()
            )

            embed.set_thumbnail(url=message.author.display_avatar.url)

            await channel.send(embed=embed)

    await bot.process_commands(message)






bot.run(os.getenv("TOKEN"))


#bot.run(token) #(toujours a la fin)



