import discord
from discord.ext import commands
import os
from datetime import datetime, timezone
import json

#client.run(token) (a la fin tjrs)
#token =

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)



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
    guild = bot.guilds[0]
    date = datetime.now(timezone.utc)

    bot.add_view(TicketView())
    print(f"\n\n=======================\n{date}\n\n{bot.user} est connecté !\n|||||||||||||||||||||||\n-")
    await log_message_bot(bot,guild,f">>> ==========================\n{date}\n\n{bot.user} est connecté !\n==========================\n|||")


@bot.event
async def on_disconnect():
    guild = bot.guilds[0]
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
async def depuis(ctx, membre: discord.Member = None):
    if membre is None:
        membre = ctx.author

    datejoin = membre.joined_at.strftime("%d/%m/%Y à %H:%M")
    await ctx.send(f"{membre.display_name} a rejoint le serveur le : {datejoin}")

@bot.command()
@commands.has_permissions(administrator=True)
async def ouvrirunticket(ctx):
    await ctx.send(
        "🎟️ **Support Tickets**\n\nClique sur le bouton pour ouvrir un ticket.\n\n",
        view=TicketView()
    )



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


@bot.event
async def on_member_remove(member):
    guild = member.guild

    if member.joined_at:
        duration = datetime.now(timezone.utc) - member.joined_at

        datejoin = member.joined_at
        date = datetime.now(timezone.utc)

        days = duration.days
        hours = duration.seconds //3600
        minutes = (duration.seconds // 60) % 60
        seconds = duration.seconds - (((duration.seconds // 60) % 60) * 60)
        totalseconds = duration.seconds

        print(f"--> {date}, {member} a quitte le serveur \nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s  ({totalseconds}s au total), {member.guild.member_count} membres")
        await log_message_JL(
            bot,
            guild, 
            f">>> --------------------------\n{date}\n\n{member} a quitte le serveur\nRejoint : {datejoin}\nLà depuis {days}j {hours}h {minutes}m {seconds}s\n{totalseconds}s au total\n{member.guild.member_count} membres à présent\n--------------------------")



#------------------SALONS VOCAUX TEMPORAIRES-----------------------------

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    create_channel = discord.utils.get(guild.voice_channels, name="Créez votre salon")\

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


    if before.channel:
        print(f"\n--> {datetime.now(timezone.utc)} {member} a quitté : {before.channel.name}")
        await log_message_voc(
            bot,
            guild, 
            f">>> __________________________\n{datetime.now(timezone.utc)}\n\n{member} a quitté : {before.channel.name}")
        

    elif after.channel and after.channel != create_channel:
        print(f"--> {datetime.now(timezone.utc)} {member} a rejoint : {after.channel.name}")
        await log_message_voc(
            bot,
            guild, 
            f">>> __________________________\n{datetime.now(timezone.utc)}\n\n{member} a rejoint : {after.channel.name}")
        

    channel = before.channel

    if channel and channel.name.startswith("🔊 vocal-"):
        try:
            if len(channel.members) == 0:
                await channel.delete()
                print(f"--> {datetime.now(timezone.utc)} supprimé : {channel.name}")
                await log_message_voc(
                    bot,
                    guild, 
                    f">>> __________________________\n{datetime.now(timezone.utc)}\n\nSupprimé : {channel.name}")
                
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
            f">>> ===__OPEN__===\n{datetime.now(timezone.utc)}\n\nTicket créé : {channel.name}\nPar {member} | ID: {channel.id}"
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


bot.run(os.getenv("TOKEN"))
