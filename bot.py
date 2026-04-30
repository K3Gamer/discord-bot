import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== CONFIG ======
OWNER_ID = 1146701570688430201

private_channels = set()

SUPER_ROLE_NAME = "🌟Super Member"
HOCBA_ROLE_NAME = "📖Học Bá"
SUPER_TIME = 60  # 3 ngày

super_data = {}
super_tasks = {}

# ====== BAD WORD ======
bad_words = [
    "dm","đm","dmm","dcm","cc","cl","lồn","cặc","địt","đụ"
]

# ====== GET ROLE ======
def get_role(guild, role_name):
    return discord.utils.get(guild.roles, name=role_name)

# ====== TIMER ======
async def super_timer(member):
    user_id = member.id

    while True:
        if user_id not in super_data:
            return

        data = super_data[user_id]

        # pause
        if not data["active"]:
            await asyncio.sleep(1)
            continue

        # hết thời gian
        if data["remaining"] <= 0:
            role = get_role(member.guild, SUPER_ROLE_NAME)

            try:
                if role and role in member.roles:
                    await member.remove_roles(role)
            except Exception as e:
                print("Lỗi remove role:", e)

            del super_data[user_id]
            super_tasks.pop(user_id, None)

            try:
                await member.send("⏰ Super Member của bạn đã hết hạn!")
            except:
                pass

            return

        await asyncio.sleep(1)
        data["remaining"] -= 1

# ====== ON MESSAGE ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # DM forward
    if isinstance(message.channel, discord.DMChannel):
        try:
            owner = await bot.fetch_user(OWNER_ID)
            dm_channel = owner.dm_channel or await owner.create_dm()

            await dm_channel.send(
                f"📩 {message.author} ({message.author.id}):\n{message.content}"
            )
        except Exception as e:
            print("DM lỗi:", e)

        return

    # command !
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # filter
    if message.channel.id not in private_channels:
        content = message.content.lower()

        if any(f" {word} " in f" {content} " for word in bad_words):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
            return

    await bot.process_commands(message)

# ====== CHAT ======
@bot.command()
async def chat(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

# ====== NR ======
@bot.command(name="nr")
async def noilai(ctx, user_input, *, message):
    await ctx.message.delete()

    try:
        user_id = int(user_input.replace("<@", "").replace(">", "").replace("!", ""))
        user = await bot.fetch_user(user_id)

        dm_channel = user.dm_channel or await user.create_dm()
        await dm_channel.send(message)

        msg = await ctx.send(f"📩 Đã gửi DM cho <@{user_id}>")
        await msg.delete(delay=3)

    except:
        msg = await ctx.send("❌ Sai cú pháp hoặc không gửi được DM")
        await msg.delete(delay=3)

# ====== FORMAT ======
def format_lines(text):
    return "\n".join(line.strip() for line in text.split(";"))

# ====== BÀI TẬP ======
@bot.command(name="bt")
async def baitap(ctx, date, so_mon: int, *, noidung):
    await ctx.message.delete()

    lines = noidung.split(";")
    if len(lines) != so_mon:
        return await ctx.send(f"❌ Bạn ghi {so_mon} môn nhưng nhập {len(lines)} dòng!")

    embed = discord.Embed(
        title=f"📚 BÀI TẬP ({date})",
        description=format_lines(noidung),
        color=0x00ffcc
    )
    embed.set_footer(text=f"Từ {ctx.author}")
    await ctx.send(embed=embed)

# ====== BÁO BÀI ======
@bot.command(name="bb")
async def baobai(ctx, so_mon: int, *, noidung):
    await ctx.message.delete()

    lines = noidung.split(";")
    if len(lines) != so_mon:
        return await ctx.send(f"❌ Bạn ghi {so_mon} môn nhưng nhập {len(lines)} dòng!")

    embed = discord.Embed(
        title="📢 BÁO BÀI",
        description=format_lines(noidung),
        color=0xffcc00
    )
    embed.set_footer(text=f"Từ {ctx.author}")
    await ctx.send(embed=embed)

# ====== CLEAR ======
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = None):
    await ctx.message.delete()

    if amount is None:
        deleted = await ctx.channel.purge(limit=1000)
    else:
        deleted = await ctx.channel.purge(limit=amount)

    msg = await ctx.send(f"🧹 Đã xoá {len(deleted)} tin nhắn")
    await msg.delete(delay=3)

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
            dm_channel = owner.dm_channel or await owner.create_dm()

            await dm_channel.send(
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

# ====== SLASH COMMAND ======
@bot.tree.command(name="supermember", description="Bật/tắt Super Member")
@app_commands.describe(mode="on hoặc off")
async def supermember(interaction: discord.Interaction, mode: str):
    member = interaction.user
    guild = interaction.guild

    hocba_role = get_role(guild, HOCBA_ROLE_NAME)
    super_role = get_role(guild, SUPER_ROLE_NAME)

    if hocba_role not in member.roles:
        return await interaction.response.send_message("❌ Bạn không phải Học Bá!", ephemeral=True)

    user_id = member.id

    if user_id not in super_data:
        super_data[user_id] = {
            "remaining": SUPER_TIME,
            "active": False
        }

    data = super_data[user_id]

    # ===== ON =====
    if mode.lower() == "on":
        if data["remaining"] <= 0:
            return await interaction.response.send_message("❌ Hết thời gian!", ephemeral=True)

        if data["active"]:
            return await interaction.response.send_message("⚠️ Đang bật rồi!", ephemeral=True)

        data["active"] = True

        if super_role not in member.roles:
            await member.add_roles(super_role)

        # chống spam task
        if user_id not in super_tasks:
            task = bot.loop.create_task(super_timer(member))
            super_tasks[user_id] = task

        await interaction.response.send_message(
            f"✅ Bật thành công!\n⏳ Còn {data['remaining']} giây",
            ephemeral=True
        )

    # ===== OFF =====
    elif mode.lower() == "off":
        data["active"] = False

        if super_role in member.roles:
            await member.remove_roles(super_role)

        await interaction.response.send_message(
            "⏸️ Đã tạm dừng và gỡ Super Member",
            ephemeral=True
        )

    else:
        await interaction.response.send_message("❌ /supermember on hoặc off", ephemeral=True)

# ====== READY ======
@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    bot.add_view(SuggestView())
    await bot.tree.sync()

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
