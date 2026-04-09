import discord
from discord.ext import commands
from datetime import datetime
import re
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== DATA ======
user_text_channels = {}
user_voice_channels = {}

# ====== BAD WORD ======
bad_words = [
    "dm","đm","dmm","dmmm","cc","vl","ngu","dcm",
    "cặc","cac","cak","c@c","c4c",
    "cu","lồn","lon","l0n","l.o.n",
    "đụ","dit","djt","đjt",
    "fuck","bitch","shit",
    "buồi","chịch","đéo","deo","deos",
    "hâm","óc chó","oc cho"
]

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ ]', '', text)
    return text

def censor_text(text):
    norm = normalize(text)
    for word in bad_words:
        if word in norm:
            return "#" * len(text)
    return text

# ====== TABLE ======
def tao_bang(title, date, data):
    mon_list = data.split(";")
    subjects, contents = [], []

    for mon in mon_list:
        if ":" in mon:
            ten, nd = mon.split(":",1)
            subjects.append(ten.strip())
            contents.append(nd.strip())

    if not subjects:
        return "❌ Không có dữ liệu!"

    max_sub = max(len(s) for s in subjects)
    max_con = max(len(c) for c in contents)

    msg = "=============================\n"
    msg += f"{title} ({date})\n"
    msg += "=============================\n"
    msg += f"{'Môn'.ljust(max_sub)} | {'Nội dung'.ljust(max_con)}\n"
    msg += "-"*(max_sub + max_con + 3) + "\n"

    for s,c in zip(subjects, contents):
        msg += f"{s.ljust(max_sub)} | {c.ljust(max_con)}\n"

    msg += "============================="
    return msg

# ====== READY ======
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

# ====== MESSAGE ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ❌ KHÔNG LỌC trong kênh 💬
    if message.channel.name.startswith("💬"):
        await bot.process_commands(message)
        return

    # ✅ LỌC ở kênh thường
    censored = censor_text(message.content)
    if censored != message.content:
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention}: {censored}", delete_after=5)
        except:
            pass
        return

    await bot.process_commands(message)

# ====== AUTO CREATE ======
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    trigger_voice = "➕Nhấn để tạo Voice"
    trigger_chat = "➕Nhấn vào đây để tạo Chat"

    if after.channel and after.channel.name == trigger_voice:
        vc = await guild.create_voice_channel(f"🎙️ {member.name}", category=after.channel.category)
        user_voice_channels[member.id] = vc.id
        await member.move_to(vc)

    if after.channel and after.channel.name == trigger_chat:
        category = discord.utils.get(guild.categories, name="Chat")
        tc = await guild.create_text_channel(f"💬-{member.name}".lower(), category=category)
        user_text_channels[member.id] = tc.id
        await member.move_to(None)
        await tc.send(f"👋 {member.mention}")

    if before.channel and before.channel.name.startswith("🎙️") and len(before.channel.members) == 0:
        cid = before.channel.id
        await before.channel.delete()

        for uid, vid in list(user_voice_channels.items()):
            if vid == cid:
                del user_voice_channels[uid]

# ====== BB ======
@bot.command()
async def bb(ctx, so_mon: int, *, data):
    await ctx.message.delete()
    today = datetime.now().strftime("%d/%m/%Y")
    msg = tao_bang("BÁO BÀI NGÀY", today, data)
    await ctx.send(f"```\n{msg}\n```")

# ====== BT ======
@bot.command()
async def bt(ctx, date: str, so_mon: int, *, data):
    await ctx.message.delete()
    msg = tao_bang("BÀI TẬP", date, data)
    await ctx.send(f"```\n{msg}\n```")

# ====== RENAME ======
@bot.command()
async def rename(ctx, *, name):
    await ctx.message.delete()

    if ctx.channel.name == "⚙️cài-đặt-kênh-chat":
        tc = ctx.guild.get_channel(user_text_channels.get(ctx.author.id))
        vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))

        if tc: await tc.edit(name=f"💬-{name}".lower())
        if vc: await vc.edit(name=f"🎙️ {name}")

    elif ctx.channel.name == "⚙️cài-đặt-kênh-voice":
        vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
        if vc: await vc.edit(name=f"🎙️ {name}")

    msg = await ctx.send("✅ Đã đổi tên")
    await msg.delete(delay=5)

# ====== PRIVATE ======
@bot.command()
async def private(ctx):
    await ctx.message.delete()

    if ctx.channel.name == "⚙️cài-đặt-kênh-chat":
        ch = ctx.guild.get_channel(user_text_channels.get(ctx.author.id))

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for role in ctx.guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=False)

        await ch.edit(overwrites=overwrites)

    elif ctx.channel.name == "⚙️cài-đặt-kênh-voice":
        ch = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=False),
            ctx.author: discord.PermissionOverwrite(connect=True, speak=True)
        }

        for role in ctx.guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(connect=False)

        await ch.edit(overwrites=overwrites)

    msg = await ctx.send("🔒 Private ON")
    await msg.delete(delay=5)

# ====== UNPRIVATE ======
@bot.command()
async def unprivate(ctx):
    await ctx.message.delete()

    if ctx.channel.name == "⚙️cài-đặt-kênh-chat":
        ch = ctx.guild.get_channel(user_text_channels.get(ctx.author.id))

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        await ch.edit(overwrites=overwrites)

    elif ctx.channel.name == "⚙️cài-đặt-kênh-voice":
        ch = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=True, speak=True)
        }

        await ch.edit(overwrites=overwrites)

    msg = await ctx.send("🔓 Private OFF")
    await msg.delete(delay=5)

# ====== ADD ======
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.message.delete()

    if ctx.channel.name == "⚙️cài-đặt-kênh-chat":
        ch = ctx.guild.get_channel(user_text_channels.get(ctx.author.id))
        await ch.set_permissions(member, read_messages=True, send_messages=True)

    elif ctx.channel.name == "⚙️cài-đặt-kênh-voice":
        ch = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
        await ch.set_permissions(member, connect=True, speak=True)

    msg = await ctx.send(f"✅ Added {member.mention}")
    await msg.delete(delay=5)

# ====== BLOCK ======
@bot.command()
async def block(ctx, member: discord.Member):
    await ctx.message.delete()

    if ctx.channel.name == "⚙️cài-đặt-kênh-chat":
        ch = ctx.guild.get_channel(user_text_channels.get(ctx.author.id))
        await ch.set_permissions(member, overwrite=None)

    elif ctx.channel.name == "⚙️cài-đặt-kênh-voice":
        ch = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
        await ch.set_permissions(member, overwrite=None)

    msg = await ctx.send(f"🚫 Blocked {member.mention}")
    await msg.delete(delay=5)

# ====== DELETE ======
@bot.command()
async def delete(ctx):
    await ctx.message.delete()

    if ctx.channel.name == "⚙️cài-đặt-kênh-chat":
        ch = ctx.guild.get_channel(user_text_channels.get(ctx.author.id))
        if ch:
            await ch.delete()
            del user_text_channels[ctx.author.id]

    elif ctx.channel.name == "⚙️cài-đặt-kênh-voice":
        ch = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
        if ch:
            await ch.delete()
            del user_voice_channels[ctx.author.id]

    msg = await ctx.send("🗑️ Deleted")
    await msg.delete(delay=5)

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))