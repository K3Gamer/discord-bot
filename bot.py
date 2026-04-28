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

            dm_channel = owner.dm_channel
            if dm_channel is None:
                dm_channel = await owner.create_dm()

            await dm_channel.send(
                f"📩 {message.author} ({message.author.id}):\n{message.content}"
            )

        except Exception as e:
            print("DM lỗi:", e)

        return  # DM không xử lý command

    # ====== FILTER ======
    if message.channel.id not in private_channels:
        content = message.content.lower()

        if any(re.search(rf"\b{re.escape(word)}\b", content) for word in bad_words):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
            return

    # ====== QUAN TRỌNG ======
    await bot.process_commands(message)

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

# ====== GÓP Ý MODAL ======
class SuggestModal(discord.ui.Modal, title="📬 Góp ý"):
    content = discord.ui.TextInput(
        label="Nhập góp ý của bạn",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        # ====== Gửi vào kênh ======
        channel = discord.utils.get(guild.text_channels, name=SUGGEST_CHANNEL_NAME)

        embed = discord.Embed(
            title="📬 Góp ý mới",
            description=self.content.value,
            color=0x00ffcc
        )
        embed.set_footer(text=f"Từ {interaction.user}")

        if channel:
            await channel.send(embed=embed)

        # ====== Gửi DM cho OWNER ======
        try:
            owner = await bot.fetch_user(OWNER_ID)

            dm_channel = owner.dm_channel
            if dm_channel is None:
                dm_channel = await owner.create_dm()

            await dm_channel.send(
                f"📬 GÓP Ý TỪ {interaction.user} ({interaction.user.id}):\n{self.content.value}"
            )

        except Exception as e:
            print("Lỗi gửi DM góp ý:", e)

        await interaction.response.send_message("✅ Đã gửi góp ý!", ephemeral=True)

# ====== VIEW ======
class SuggestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📬 Gửi góp ý", style=discord.ButtonStyle.primary, custom_id="suggest_btn")
    async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestModal())

# ====== LỆNH GÓP Ý ======
@bot.command(name="gopy")
async def gopy(ctx):
    await ctx.message.delete()

    embed = discord.Embed(
        title="📬 Hộp thư góp ý",
        description="Nhấn nút bên dưới để gửi góp ý",
        color=0x00ffcc
    )

    await ctx.send(embed=embed, view=SuggestView())

# ====== READY ======
@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    bot.add_view(SuggestView())

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
