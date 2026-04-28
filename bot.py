import discord
from discord.ext import commands
import os
import re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== CONFIG ======
SUGGEST_CHANNEL_NAME = "📬hộp-thư-góp-ý📬"
OWNER_ID = 1146701570688430201

private_channels = set()

# ====== BAD WORD ======
bad_words = [
    "dm","đm","dmm","dcm","cc","cl","lồn","cặc","địt","đụ"
]

# ====== ON MESSAGE ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ====== DM FORWARD ======
    if isinstance(message.channel, discord.DMChannel):
        try:
            owner = await bot.fetch_user(OWNER_ID)
            await owner.send(f"📩 {message.author}:\n{message.content}")
        except:
            pass
        return

    # ====== COMMAND ======
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # ====== FILTER ======
    if message.channel.id not in private_channels:
        content = message.content.lower()

        if any(re.search(rf"\b{re.escape(word)}\b", content) for word in bad_words):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
            return

    await bot.process_commands(message)

# ====== PRIVATE ======
@bot.command()
async def private(ctx):
    await ctx.message.delete()
    private_channels.add(ctx.channel.id)
    await ctx.send("🔒 Đã bật private")

@bot.command()
async def unprivate(ctx):
    await ctx.message.delete()
    private_channels.discard(ctx.channel.id)
    await ctx.send("🔓 Đã tắt private")

# ====== CHAT ======
@bot.command()
async def chat(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

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

# ====== CLEAR USER ======
@bot.command(name="clearuser")
@commands.has_permissions(manage_messages=True)
async def clearuser(ctx, member: discord.Member, amount: int = None):
    await ctx.message.delete()

    def check(m):
        return m.author == member

    if amount is None:
        deleted = await ctx.channel.purge(limit=1000, check=check)
    else:
        deleted = await ctx.channel.purge(limit=amount, check=check)

    msg = await ctx.send(f"🧹 Đã xoá {len(deleted)} tin của {member.mention}")
    await msg.delete(delay=3)

# ====== GÓP Ý MODAL ======
class SuggestModal(discord.ui.Modal, title="📬 Góp ý ẩn danh"):
    content = discord.ui.TextInput(
        label="Nhập góp ý của bạn",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = discord.utils.get(interaction.guild.text_channels, name=SUGGEST_CHANNEL_NAME)

        if not channel:
            return await interaction.response.send_message("❌ Không tìm thấy kênh góp ý", ephemeral=True)

        embed = discord.Embed(
            title="📬 Góp ý mới",
            description=self.content.value,
            color=0x00ffcc
        )

        embed.set_footer(text="Ẩn danh")
        await channel.send(embed=embed)

        await interaction.response.send_message("✅ Đã gửi góp ý!", ephemeral=True)

# ====== VIEW ======
class SuggestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📬 Gửi góp ý", style=discord.ButtonStyle.primary, custom_id="suggest_btn")
    async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestModal())

# ====== LỆNH PANEL ======
@bot.command()
async def goiy(ctx):
    await ctx.message.delete()

    embed = discord.Embed(
        title="📬 Hộp thư góp ý",
        description="Nhấn nút bên dưới để gửi góp ý (ẩn danh)",
        color=0x00ffcc
    )

    await ctx.send(embed=embed, view=SuggestView())

# ====== READY ======
@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    bot.add_view(SuggestView())

# ====== WELCOME ======
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="👋・welcome")
    if channel:
        await channel.send(f"👋 Chào mừng {member.mention}!")

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
