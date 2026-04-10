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

# ====== READY ======
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

# ====== FILTER ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    censored = censor_text(message.content)
    if censored != message.content:
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention}: {censored}", delete_after=5)
        except:
            pass
        return

    await bot.process_commands(message)

# ====== AUTO CREATE VOICE ======
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    trigger_voice = "➕Nhấn để tạo Voice"

    # tạo room
    if after.channel and after.channel.name == trigger_voice:
        vc = await guild.create_voice_channel(f"🎙️ {member.name}", category=after.channel.category)
        user_voice_channels[member.id] = vc.id
        await member.move_to(vc)

    # auto delete khi rỗng
    if before.channel and before.channel.name.startswith("🎙️") and len(before.channel.members) == 0:
        cid = before.channel.id
        await before.channel.delete()

        for uid, vid in list(user_voice_channels.items()):
            if vid == cid:
                del user_voice_channels[uid]

# ====== UI MESSAGE ======
async def send_voice_ui(channel):
    msg = """
🎛️ **VOICE CONTROL PANEL**

!rename <tên> → Đổi tên phòng
!private → Khoá phòng
!unprivate → Mở phòng
!add @user → Thêm người
!block @user → Kick quyền người đó
!delete → Xoá phòng

⚠️ Chỉ dùng trong kênh này!
"""
    await channel.send(f"```\n{msg}\n```")

# ====== RESET UI ======
@bot.command()
async def resetUIvoice(ctx):
    await ctx.message.delete()

    await ctx.channel.purge(limit=20)
    await send_voice_ui(ctx.channel)

# ====== RENAME ======
@bot.command()
async def rename(ctx, *, name):
    await ctx.message.delete()

    vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
    if vc:
        await vc.edit(name=f"🎙️ {name}")

    msg = await ctx.send("✅ Đã đổi tên")
    await msg.delete(delay=5)

# ====== PRIVATE ======
@bot.command()
async def private(ctx):
    await ctx.message.delete()

    vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(connect=False),
        ctx.author: discord.PermissionOverwrite(connect=True, speak=True)
    }

    await vc.edit(overwrites=overwrites)

    msg = await ctx.send("🔒 Private ON")
    await msg.delete(delay=5)

# ====== UNPRIVATE ======
@bot.command()
async def unprivate(ctx):
    await ctx.message.delete()

    vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(connect=True, speak=True)
    }

    await vc.edit(overwrites=overwrites)

    msg = await ctx.send("🔓 Private OFF")
    await msg.delete(delay=5)

# ====== ADD ======
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.message.delete()

    vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
    await vc.set_permissions(member, connect=True, speak=True)

    msg = await ctx.send(f"✅ Added {member.mention}")
    await msg.delete(delay=5)

# ====== BLOCK ======
@bot.command()
async def block(ctx, member: discord.Member):
    await ctx.message.delete()

    vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
    await vc.set_permissions(member, connect=False)

    msg = await ctx.send(f"🚫 Blocked {member.mention}")
    await msg.delete(delay=5)

# ====== DELETE ======
@bot.command()
async def delete(ctx):
    await ctx.message.delete()

    vc = ctx.guild.get_channel(user_voice_channels.get(ctx.author.id))
    if vc:
        await vc.delete()
        del user_voice_channels[ctx.author.id]

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
