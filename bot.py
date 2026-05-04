import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import json
import time

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== CONFIG =====
OWNER_ID = 1146701570688430201

SUPER_ROLE_NAME = "🌟Super Member"
HOCBA_ROLE_NAME = "📖Học Bá"
BIRTHDAY_ROLE_NAME = "🎉Birthday"
RESTRICTED_ROLE_NAME = "🚫Restricted"
BOT_ROLE_NAME = "🧠Bot"

DATA_FILE = "super_data.json"
BIRTHDAY_FILE = "birthday.json"
AIHOI_FILE = "aihoi.json"

TARGET_USER_ID = 1499725865511030895

trigger_words = [
    "ai hỏi", "ai hoi", "who asked",
    "ko ai hỏi", "không ai hỏi"
]

birthday_data = {}
aihoi_settings = {}
restricted_cooldown = {}

# ================= LOAD SAVE =================

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_all():
    global birthday_data, aihoi_settings
    birthday_data = load_json(BIRTHDAY_FILE)
    aihoi_settings = load_json(AIHOI_FILE)

def save_birthday():
    save_json(BIRTHDAY_FILE, birthday_data)

def save_aihoi():
    save_json(AIHOI_FILE, aihoi_settings)

# ================= ROLE =================

def get_role(guild, name):
    return discord.utils.get(guild.roles, name=name)

# ================= AIHOI =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        return

    content = message.content.lower()
    guild = message.guild

    enabled = aihoi_settings.get(str(guild.id), False)

    if enabled and message.author.id == TARGET_USER_ID:
        if any(word in content for word in trigger_words):

            now = time.time()
            if message.author.id in restricted_cooldown:
                if now - restricted_cooldown[message.author.id] < 5:
                    return
            restricted_cooldown[message.author.id] = now

            restricted_role = get_role(guild, RESTRICTED_ROLE_NAME)
            bot_role = get_role(guild, BOT_ROLE_NAME)

            if not restricted_role:
                restricted_role = await guild.create_role(name=RESTRICTED_ROLE_NAME)

            # nếu đang bị rồi thì bỏ qua
            if restricted_role in message.author.roles:
                return

            # remove bot role
            if bot_role and bot_role in message.author.roles:
                try:
                    await message.author.remove_roles(bot_role)
                except:
                    pass

            # add restricted
            try:
                await message.author.add_roles(restricted_role)
            except:
                pass

            await message.channel.send(f"🚫 {message.author.mention} bị Restricted 3 giây!")

            await asyncio.sleep(3)

            # restore
            try:
                await message.author.remove_roles(restricted_role)
            except:
                pass

            if bot_role:
                try:
                    await message.author.add_roles(bot_role)
                except:
                    pass

    await bot.process_commands(message)

# ================= COMMAND =================

@bot.tree.command(name="allowaihoi")
async def allowaihoi(interaction: discord.Interaction, mode: str):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ No perm", ephemeral=True)

    gid = str(interaction.guild.id)

    if mode.lower() == "on":
        aihoi_settings[gid] = True
        save_aihoi()
        await interaction.response.send_message("✅ ON", ephemeral=True)

    elif mode.lower() == "off":
        aihoi_settings[gid] = False
        save_aihoi()
        await interaction.response.send_message("⛔ OFF", ephemeral=True)

    else:
        await interaction.response.send_message("❌ on/off", ephemeral=True)

# ================= BIRTHDAY =================

@bot.tree.command(name="setbirthday")
async def setbirthday(interaction: discord.Interaction, member: discord.Member, date: str):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ No perm", ephemeral=True)

    try:
        d = int(date[:2])
        m = int(date[2:4])
        y = int(date[4:])
    except:
        return await interaction.response.send_message("❌ DDMMYYYY", ephemeral=True)

    birthday_data[str(member.id)] = {
        "day": d,
        "month": m,
        "year": y,
        "last_year": 0
    }

    save_birthday()
    await interaction.response.send_message("🎂 Set xong", ephemeral=True)

# ===== donsinhnhat =====

@bot.tree.command(name="donsinhnhat")
async def donsinhnhat(interaction: discord.Interaction):

    guild = interaction.guild
    d = int(time.strftime("%d"))
    m = int(time.strftime("%m"))
    y = int(time.strftime("%Y"))

    role = get_role(guild, BIRTHDAY_ROLE_NAME)
    if not role:
        role = await guild.create_role(name=BIRTHDAY_ROLE_NAME)

    found = False

    for member in guild.members:
        uid = str(member.id)

        if uid not in birthday_data:
            continue

        data = birthday_data[uid]

        if data["day"] == d and data["month"] == m:

            if data["last_year"] == y:
                continue

            found = True
            age = y - data["year"]

            await member.add_roles(role)

            await interaction.channel.send(
                f"🎉 {member.mention} sinh nhật {age} tuổi!"
            )

            birthday_data[uid]["last_year"] = y

    save_birthday()

    await interaction.response.send_message(
        "🎂 Done" if found else "😴 No birthday",
        ephemeral=True
    )

# ===== LIST SINH NHẬT =====

@bot.tree.command(name="listsinhnhat")
async def listsinhnhat(interaction: discord.Interaction):

    if not birthday_data:
        return await interaction.response.send_message("❌ Chưa có data", ephemeral=True)

    msg = "📜 DANH SÁCH SINH NHẬT:\n\n"

    for uid, data in birthday_data.items():
        member = interaction.guild.get_member(int(uid))
        name = member.name if member else f"ID:{uid}"

        msg += f"👤 {name} - {data['day']:02d}/{data['month']:02d}/{data['year']}\n"

    await interaction.response.send_message(msg, ephemeral=True)

# ================= READY =================

@bot.event
async def on_ready():
    print("Bot online:", bot.user)

    load_all()
    await bot.tree.sync()

# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))
