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

def format_time(sec):
    d = sec // 86400
    h = (sec % 86400) // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{d}d {h}h {m}m {s}s"

def format_lines(text):
    return "\n".join(line.strip() for line in text.split(";"))

# =========================
# CHAT FILTER + DM FORWARD
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

    # filter
    content = message.content.lower()
    if any(f" {w} " in f" {content} " for w in bad_words):
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
        return

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

@bot.command(name="nr")
async def noilai(ctx, user_input, *, message):
    await ctx.message.delete()
    try:
        uid = int(user_input.replace("<@", "").replace(">", "").replace("!", ""))
        user = await bot.fetch_user(uid)
        dm = user.dm_channel or await user.create_dm()
        await dm.send(message)
    except:
        await ctx.send("❌ Lỗi")

@bot.command(name="bt")
async def baitap(ctx, date, so_mon: int, *, noidung):
    await ctx.message.delete()
    lines = noidung.split(";")
    if len(lines) != so_mon:
        return await ctx.send("❌ Sai số môn")

    embed = discord.Embed(
        title=f"📚 BÀI TẬP ({date})",
        description=format_lines(noidung),
        color=0x00ffcc
    )
    await ctx.send(embed=embed)

@bot.command(name="bb")
async def baobai(ctx, so_mon: int, *, noidung):
    await ctx.message.delete()
    lines = noidung.split(";")
    if len(lines) != so_mon:
        return await ctx.send("❌ Sai số môn")

    embed = discord.Embed(
        title="📢 BÁO BÀI",
        description=format_lines(noidung),
        color=0xffcc00
    )
    await ctx.send(embed=embed)

# =========================
# SUPER SYSTEM
# =========================
async def super_timer(member):
    uid = str(member.id)
    while True:
        if uid not in super_data:
            return

        data = super_data[uid]

        if not data["active"]:
            await asyncio.sleep(1)
            continue

        now = int(time.time())
        elapsed = now - data["last_time"]
        data["last_time"] = now
        data["remaining"] -= elapsed

        if data["remaining"] <= 0:
            role = get_role(member.guild, SUPER_ROLE_NAME)
            try:
                if role in member.roles:
                    await member.remove_roles(role)
            except:
                pass

            del super_data[uid]
            save_data()
            super_tasks.pop(uid, None)

            try:
                await member.send("⏰ Super Member đã hết hạn!")
            except:
                pass
            return

        save_data()
        await asyncio.sleep(1)

# =========================
# BIRTHDAY SYSTEM
# =========================
async def birthday_checker():
    await bot.wait_until_ready()
    while not bot.is_closed():
        day = int(time.strftime("%d"))
        month = int(time.strftime("%m"))
        year = int(time.strftime("%Y"))

        for guild in bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="🗨️nhắn-tin💬")
            if not channel:
                continue

            role = discord.utils.get(guild.roles, name=BIRTHDAY_ROLE_NAME)
            if not role:
                role = await guild.create_role(name=BIRTHDAY_ROLE_NAME)

            for member in guild.members:
                uid = str(member.id)
                if uid not in birthday_data:
                    continue

                data = birthday_data[uid]

                if data["day"] == day and data["month"] == month:
                    if data.get("last_year") == year:
                        continue

                    age = year - data["year"]

                    try:
                        await member.add_roles(role)
                    except:
                        pass

                    embed = discord.Embed(
                        title="🎉 CHÚC MỪNG SINH NHẬT 🎂",
                        description=f"Hôm nay là ngày sinh nhật thứ **{age}** của **{member.name}** 🎊",
                        color=0xffcc00
                    )

                    avatar = member.avatar.url if member.avatar else member.default_avatar.url
                    embed.set_thumbnail(url=avatar)

                    await channel.send(content=member.mention, embed=embed)

                    if uid not in super_data:
                        super_data[uid] = {
                            "remaining": 3 * 86400,
                            "active": False,
                            "last_time": int(time.time())
                        }
                    else:
                        super_data[uid]["remaining"] += 3 * 86400

                    save_data()

                    birthday_data[uid]["last_year"] = year
                    save_birthday()

                    try:
                        await member.send("🎁 Bạn được tặng +3 ngày Super Member!")
                    except:
                        pass

        await asyncio.sleep(60 * 60 * 24)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    load_data()
    load_birthday()

    bot.loop.create_task(birthday_checker())

    for uid in list(super_data.keys()):
        for guild in bot.guilds:
            member = guild.get_member(int(uid))
            if member:
                super_tasks[uid] = bot.loop.create_task(super_timer(member))
                break

    await bot.tree.sync()

# =========================
# RUN
# =========================
bot.run(os.getenv("DISCORD_TOKEN"))
