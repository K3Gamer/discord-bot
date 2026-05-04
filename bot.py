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

BOT_ROLE_NAME = "🧠Bot"
RESTRICTED_ROLE_NAME = "🚫Restricted"
TARGET_USER_ID = 1499725865511030895

trigger_words = [
    "ai hỏi", "ai hoi", "who asked",
    "ko ai hỏi", "không ai hỏi"
]

SUPER_TIME = 3 * 24 * 60 * 60

DATA_FILE = "super_data.json"
BIRTHDAY_FILE = "birthday.json"
AIHOI_FILE = "aihoi.json"

super_data = {}
super_tasks = {}
birthday_data = {}
aihoi_settings = {}

# ===== BAD WORD =====
bad_words = ["dm","đm","dmm","dcm","cc","cl","lồn","cặc","địt","đụ"]

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
    global super_data, birthday_data, aihoi_settings
    super_data = load_json(DATA_FILE)
    birthday_data = load_json(BIRTHDAY_FILE)
    aihoi_settings = load_json(AIHOI_FILE)

def save_all():
    save_json(DATA_FILE, super_data)
    save_json(BIRTHDAY_FILE, birthday_data)
    save_json(AIHOI_FILE, aihoi_settings)

# ================= ROLE =================

def get_role(guild, name):
    return discord.utils.get(guild.roles, name=name)

# ================= ANTI AMONGUS =================

async def punish_target(guild, channel):
    target = guild.get_member(TARGET_USER_ID)
    if not target:
        return

    bot_role = get_role(guild, BOT_ROLE_NAME)
    restricted_role = get_role(guild, RESTRICTED_ROLE_NAME)

    if not restricted_role:
        restricted_role = await guild.create_role(name=RESTRICTED_ROLE_NAME)

    try:
        if bot_role and bot_role in target.roles:
            await target.remove_roles(bot_role)

        if restricted_role not in target.roles:
            await target.add_roles(restricted_role)

        await channel.send(f"🚫 {target.mention} đã bị Restricted!")

    except Exception as e:
        print("PUNISH ERROR:", e)

# ================= MESSAGE =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        return

    content = message.content.lower()
    guild = message.guild

    # ===== BAD WORD =====
    if any(f" {w} " in f" {content} " for w in bad_words):
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
        return

    # ===== AIHOI SYSTEM =====
    enabled = aihoi_settings.get(str(guild.id), False)

    if enabled:
        if any(word in content for word in trigger_words):
            bot.loop.create_task(
                punish_target(guild, message.channel)
            )

    await bot.process_commands(message)

# ================= COMMAND =================

@bot.tree.command(name="allowaihoi")
async def allowaihoi(interaction: discord.Interaction, mode: str):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Không có quyền", ephemeral=True)

    gid = str(interaction.guild.id)

    if mode.lower() == "on":
        aihoi_settings[gid] = True
        save_all()
        await interaction.response.send_message("✅ Đã bật anti amongus", ephemeral=True)

    elif mode.lower() == "off":
        aihoi_settings[gid] = False
        save_all()
        await interaction.response.send_message("⛔ Đã tắt", ephemeral=True)

# ================= BIRTHDAY =================

@bot.tree.command(name="setbirthday")
async def setbirthday(interaction: discord.Interaction, member: discord.Member, date: str):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Không có quyền", ephemeral=True)

    try:
        d = int(date[:2])
        m = int(date[2:4])
        y = int(date[4:])
    except:
        return await interaction.response.send_message("❌ Format DDMMYYYY", ephemeral=True)

    birthday_data[str(member.id)] = {
        "day": d,
        "month": m,
        "year": y,
        "last_year": 0
    }

    save_all()
    await interaction.response.send_message("🎂 Đã set", ephemeral=True)

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
            await interaction.channel.send(f"🎉 {member.mention} sinh nhật {age} tuổi!")

            birthday_data[uid]["last_year"] = y

    save_all()

    await interaction.response.send_message(
        "🎂 Đã chạy!" if found else "😴 Không có ai",
        ephemeral=True
    )

# ================= READY =================

@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    load_all()
    await bot.tree.sync()

# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))
