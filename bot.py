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

# ====== CONFIG ======
OWNER_ID = 1146701570688430201

SUPER_ROLE_NAME = "🌟Super Member"
HOCBA_ROLE_NAME = "📖Học Bá"
BIRTHDAY_ROLE_NAME = "🎉Birthday"

# 🔥 NEW
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

super_data = {}
super_tasks = {}
birthday_data = {}

# ====== BAD WORD ======
bad_words = ["dm","đm","dmm","dcm","cc","cl","lồn","cặc","địt","đụ"]

# =========================
# LOAD / SAVE
# =========================

def load_data():
    global super_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            super_data = json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(super_data, f, indent=4)

def load_birthday():
    global birthday_data
    if os.path.exists(BIRTHDAY_FILE):
        with open(BIRTHDAY_FILE, "r", encoding="utf-8") as f:
            birthday_data = json.load(f)

def save_birthday():
    with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
        json.dump(birthday_data, f, indent=4)

# =========================
# ROLE
# =========================

def get_role(guild, name):
    return discord.utils.get(guild.roles, name=name)

def format_lines(text):
    return "\n".join(line.strip() for line in text.split(";"))

# =========================
# CHAT FILTER + AIHOI + DM
# =========================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # DM forward
    if isinstance(message.channel, discord.DMChannel):
        try:
            owner = await bot.fetch_user(OWNER_ID)
            dm = owner.dm_channel or await owner.create_dm()
            await dm.send(f"📩 {message.author}:\n{message.content}")
        except:
            pass
        return

    content = message.content.lower()

    # ===== FILTER =====
    if any(f" {w} " in f" {content} " for w in bad_words):
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
        return

    # ===== AI HỎI =====
    if message.author.id == TARGET_USER_ID:
        if any(word in content for word in trigger_words):

            guild = message.guild

            bot_role = get_role(guild, BOT_ROLE_NAME)
            restricted_role = get_role(guild, RESTRICTED_ROLE_NAME)

            # tạo role nếu chưa có
            if not restricted_role:
                restricted_role = await guild.create_role(name=RESTRICTED_ROLE_NAME)

            try:
                # ❌ remove 🧠Bot
                if bot_role and bot_role in message.author.roles:
                    await message.author.remove_roles(bot_role)

                # 🚫 add Restricted
                if restricted_role not in message.author.roles:
                    await message.author.add_roles(restricted_role)

                await message.channel.send(f"🚫 {message.author.mention} đã bị Restricted!")

            except Exception as e:
                print("AIHOI ERROR:", e)

    await bot.process_commands(message)

# =========================
# BASIC COMMANDS
# =========================

@bot.command()
async def chat(ctx, *, msg):
    await ctx.message.delete()
    await ctx.send(msg)

@bot.command()
async def clear(ctx, amount: int = 10):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    m = await ctx.send(f"🧹 Đã xoá {len(deleted)} tin nhắn")
    await m.delete(delay=3)

# =========================
# BIRTHDAY SYSTEM
# =========================

@bot.tree.command(name="setbirthday")
async def setbirthday(interaction: discord.Interaction, member: discord.Member, date: str):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Không có quyền", ephemeral=True)

    try:
        day = int(date[0:2])
        month = int(date[2:4])
        year = int(date[4:8])
    except:
        return await interaction.response.send_message("❌ Sai format DDMMYYYY", ephemeral=True)

    birthday_data[str(member.id)] = {
        "day": day,
        "month": month,
        "year": year,
        "last_year": 0
    }

    save_birthday()
    await interaction.response.send_message("🎂 Đã set sinh nhật", ephemeral=True)

@bot.tree.command(name="donsinhnhat")
async def donsinhnhat(interaction: discord.Interaction):

    guild = interaction.guild
    today_day = int(time.strftime("%d"))
    today_month = int(time.strftime("%m"))
    year = int(time.strftime("%Y"))

    channel = discord.utils.get(guild.text_channels, name="🗨️nhắn-tin💬")

    if not channel:
        return await interaction.response.send_message("❌ Không tìm thấy kênh", ephemeral=True)

    role = get_role(guild, BIRTHDAY_ROLE_NAME)
    if not role:
        role = await guild.create_role(name=BIRTHDAY_ROLE_NAME)

    found = False

    for member in guild.members:
        uid = str(member.id)

        if uid not in birthday_data:
            continue

        data = birthday_data[uid]

        if data["day"] == today_day and data["month"] == today_month:

            if data.get("last_year") == year:
                continue

            found = True
            age = year - data["year"]

            await member.add_roles(role)

            await channel.send(f"🎉 {member.mention} sinh nhật {age} tuổi!")

            birthday_data[uid]["last_year"] = year

    save_birthday()

    await interaction.response.send_message(
        "🎂 Đã chạy!" if found else "😴 Không có ai",
        ephemeral=True
    )
@bot.command(name="antiamongus")
async def antiamongus(ctx):
    guild = ctx.guild

    member = guild.get_member(TARGET_USER_ID)
    if not member:
        return await ctx.send("❌ Không tìm thấy user")

    bot_role = get_role(guild, BOT_ROLE_NAME)
    restricted_role = get_role(guild, RESTRICTED_ROLE_NAME)

    # tạo role nếu chưa có
    if not restricted_role:
        restricted_role = await guild.create_role(name=RESTRICTED_ROLE_NAME)

    try:
        # ❌ remove 🧠Bot
        if bot_role and bot_role in member.roles:
            await member.remove_roles(bot_role)

        # 🚫 add Restricted
        if restricted_role not in member.roles:
            await member.add_roles(restricted_role)

        await ctx.send(f"🚫 {member.mention} đã bị Restricted bởi lệnh!")

    except Exception as e:
        print("ANTI AMONGUS ERROR:", e)
        await ctx.send("❌ Lỗi khi xử lý")

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print("Bot online:", bot.user)

    load_data()
    load_birthday()

    await bot.tree.sync()

# =========================
# RUN
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))
