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
RESTRICTED_ROLE_NAME = "🚫Restricted"

SUPER_TIME = 3 * 24 * 60 * 60

DATA_FILE = "super_data.json"
BIRTHDAY_FILE = "birthday.json"
AIHOI_FILE = "aihoi.json"

TARGET_USER_ID = 1499725865511030895

trigger_words = [
    "ai hỏi",
    "ai hoi",
    "who asked",
    "ko ai hỏi",
    "không ai hỏi"
]

super_data = {}
super_tasks = {}
birthday_data = {}
aihoi_settings = {}
restricted_cooldown = {}

# ====== BAD WORD ======
bad_words = ["dm","đm","dmm","dcm","cc","cl","lồn","cặc","địt","đụ"]

# =========================
# LOAD / SAVE
# =========================

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_data():
    global super_data
    super_data = load_json(DATA_FILE)

def save_data():
    save_json(DATA_FILE, super_data)

def load_birthday():
    global birthday_data
    birthday_data = load_json(BIRTHDAY_FILE)

def save_birthday():
    save_json(BIRTHDAY_FILE, birthday_data)

def load_aihoi():
    global aihoi_settings
    aihoi_settings = load_json(AIHOI_FILE)

def save_aihoi():
    save_json(AIHOI_FILE, aihoi_settings)

# =========================
# ROLE
# =========================

def get_role(guild, name):
    return discord.utils.get(guild.roles, name=name)

def format_lines(text):
    return "\n".join(line.strip() for line in text.split(";"))

# =========================
# ON MESSAGE
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

    # ===== AI HỎI SYSTEM =====
    guild_id = str(message.guild.id)
    enabled = aihoi_settings.get(guild_id, False)

    if enabled and message.author.id == TARGET_USER_ID:
        if any(word in content for word in trigger_words):

            role = get_role(message.guild, RESTRICTED_ROLE_NAME)

            if not role:
                role = await message.guild.create_role(name=RESTRICTED_ROLE_NAME)

            # 👉 FIX: chỉ xử lý nếu CHƯA có role
            if role not in message.author.roles:

                now = time.time()
                if message.author.id in restricted_cooldown:
                    if now - restricted_cooldown[message.author.id] < 5:
                        return

                restricted_cooldown[message.author.id] = now

                try:
                    await message.author.add_roles(role)
                except:
                    pass

                await message.channel.send(f"🚫 {message.author.mention} bị Restricted 2 giây!")

                await asyncio.sleep(2)

                try:
                    await message.author.remove_roles(role)
                except:
                    pass

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
# BIRTHDAY COMMANDS
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
        return await interaction.response.send_message("❌ Format DDMMYYYY", ephemeral=True)

    birthday_data[str(member.id)] = {
        "day": day,
        "month": month,
        "year": year,
        "last_year": 0
    }

    save_birthday()
    await interaction.response.send_message("🎂 Đã set", ephemeral=True)

# ===== /donsinhnhat =====

@bot.tree.command(name="donsinhnhat")
async def donsinhnhat(interaction: discord.Interaction):

    guild = interaction.guild
    today_day = int(time.strftime("%d"))
    today_month = int(time.strftime("%m"))
    year = int(time.strftime("%Y"))

    channel = discord.utils.get(guild.text_channels, name="🗨️nhắn-tin💬")
    if not channel:
        return await interaction.response.send_message("❌ Không có kênh", ephemeral=True)

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

            embed = discord.Embed(
                title="🎉 CHÚC MỪNG SINH NHẬT 🎂",
                description=f"{member.name} {age} tuổi 🎊",
                color=0xffcc00
            )

            await channel.send(content=member.mention, embed=embed)

            birthday_data[uid]["last_year"] = year

    save_birthday()

    await interaction.response.send_message(
        "🎂 Đã chạy!" if found else "😴 Không có ai",
        ephemeral=True
    )

# ===== /listsinhnhat =====

@bot.tree.command(name="listsinhnhat")
async def listsinhnhat(interaction: discord.Interaction):

    if not birthday_data:
        return await interaction.response.send_message("❌ Chưa có dữ liệu", ephemeral=True)

    text = ""

    for uid, data in birthday_data.items():
        member = interaction.guild.get_member(int(uid))
        name = member.name if member else f"ID:{uid}"
        text += f"👤 {name} - {data['day']:02d}/{data['month']:02d}/{data['year']}\n"

    await interaction.response.send_message(f"📜 DANH SÁCH:\n{text}", ephemeral=True)

# =========================
# AIHOI COMMAND
# =========================

@bot.tree.command(name="allowaihoi")
async def allowaihoi(interaction: discord.Interaction, mode: str):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Không có quyền", ephemeral=True)

    guild_id = str(interaction.guild.id)

    if mode.lower() == "on":
        aihoi_settings[guild_id] = True
        save_aihoi()
        await interaction.response.send_message("✅ ON", ephemeral=True)

    elif mode.lower() == "off":
        aihoi_settings[guild_id] = False
        save_aihoi()
        await interaction.response.send_message("⛔ OFF", ephemeral=True)

    else:
        await interaction.response.send_message("❌ on/off", ephemeral=True)

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print("Bot online:", bot.user)

    load_data()
    load_birthday()
    load_aihoi()

    await bot.tree.sync()

# =========================
# RUN
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))
