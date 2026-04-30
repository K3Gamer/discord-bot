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
private_channels = set()

SUPER_ROLE_NAME = "🌟Super Member"
HOCBA_ROLE_NAME = "📖Học Bá"
SUPER_TIME = 3 * 24 * 60 * 60

DATA_FILE = "super_data.json"

super_data = {}
super_tasks = {}

# ====== BAD WORD ======
bad_words = [
    "dm","đm","dmm","dcm","cc","cl","lồn","cặc","địt","đụ"
]

# ====== LOAD/SAVE ======
def load_data():
    global super_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            super_data = json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(super_data, f, indent=4)

# ====== ROLE ======
def get_role(guild, name):
    return discord.utils.get(guild.roles, name=name)

# ====== FORMAT TIME ======
def format_time(sec):
    d = sec // 86400
    h = (sec % 86400) // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{d}d {h}h {m}m {s}s"

# ====== TIMER ======
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
                if role and role in member.roles:
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

# ====== ON MESSAGE ======
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

    # command !
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # filter
    if message.channel.id not in private_channels:
        content = message.content.lower()
        if any(f" {w} " in f" {content} " for w in bad_words):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
            return

    await bot.process_commands(message)

# ====== COMMAND CŨ ======
@bot.command()
async def chat(ctx, *, msg):
    await ctx.message.delete()
    await ctx.send(msg)

@bot.command()
async def clear(ctx, amount: int = 10):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    m = await ctx.send(f"🧹 Đã xoá {len(deleted)}")
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

def format_lines(text):
    return "\n".join(line.strip() for line in text.split(";"))

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

# ====== GÓP Ý ======
class SuggestModal(discord.ui.Modal, title="📬 Góp ý"):
    content = discord.ui.TextInput(
        label="Nhập góp ý của bạn",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            owner = await bot.fetch_user(OWNER_ID)
            dm = owner.dm_channel or await owner.create_dm()
            await dm.send(
                f"📬 GÓP Ý TỪ {interaction.user} ({interaction.user.id}):\n{self.content.value}"
            )
        except Exception as e:
            print("Lỗi góp ý:", e)

        await interaction.response.send_message("✅ Đã gửi góp ý!", ephemeral=True)

class SuggestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📬 Gửi góp ý", style=discord.ButtonStyle.primary, custom_id="suggest_btn")
    async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestModal())

@bot.command(name="gopy")
async def gopy(ctx):
    await ctx.message.delete()

    embed = discord.Embed(
        title="📬 Hộp thư góp ý",
        description="Nhấn nút bên dưới để gửi góp ý",
        color=0x00ffcc
    )

    await ctx.send(embed=embed, view=SuggestView())

# ====== SUPER MEMBER ======
@bot.tree.command(name="supermember")
async def supermember(interaction: discord.Interaction, mode: str):
    member = interaction.user
    guild = interaction.guild

    hocba = get_role(guild, HOCBA_ROLE_NAME)
    super_role = get_role(guild, SUPER_ROLE_NAME)

    if hocba not in member.roles:
        return await interaction.response.send_message("❌ Không phải Học Bá", ephemeral=True)

    uid = str(member.id)

    if uid not in super_data:
        super_data[uid] = {
            "remaining": SUPER_TIME,
            "active": False,
            "last_time": int(time.time())
        }

    data = super_data[uid]

    if mode == "on":
        if data["remaining"] <= 0:
            return await interaction.response.send_message("❌ Hết giờ", ephemeral=True)

        data["active"] = True
        data["last_time"] = int(time.time())

        if super_role not in member.roles:
            await member.add_roles(super_role)

        if uid not in super_tasks:
            super_tasks[uid] = bot.loop.create_task(super_timer(member))

        save_data()

        await interaction.response.send_message(f"✅ ON\n⏳ {format_time(data['remaining'])}", ephemeral=True)

    elif mode == "off":
        data["active"] = False
        save_data()

        if super_role in member.roles:
            await member.remove_roles(super_role)

        await interaction.response.send_message("⏸️ OFF", ephemeral=True)

# ====== STATUS ======
@bot.tree.command(name="superstatus")
async def superstatus(interaction: discord.Interaction):
    uid = str(interaction.user.id)

    if uid not in super_data:
        return await interaction.response.send_message("❌ Chưa kích hoạt", ephemeral=True)

    data = super_data[uid]
    status = "🟢 ON" if data["active"] else "⏸️ OFF"

    await interaction.response.send_message(
        f"{status}\n⏳ {format_time(int(data['remaining']))}",
        ephemeral=True
    )

# ====== READY ======
@bot.event
async def on_ready():
    print("Bot online:", bot.user)

    load_data()

    # resume timer
    for uid in list(super_data.keys()):
        for guild in bot.guilds:
            member = guild.get_member(int(uid))
            if member:
                super_tasks[uid] = bot.loop.create_task(super_timer(member))
                break

    bot.add_view(SuggestView())  # giữ button góp ý
    await bot.tree.sync()

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
