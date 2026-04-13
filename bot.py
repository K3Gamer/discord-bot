import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

VOICE_TRIGGER_NAME = "➕Nhấn để tạo Voice"
CONTROL_CHANNEL_NAME = "⚙️cài-đặt-kênh-voice"

voice_owners = {}
private_channels = set()

# ====== BAD WORD ======
bad_words = [
    "dm","đm","dmm","dcm","cc","cl","lồn","cặc","địt","đụ"
]

# ====== FILTER ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id not in private_channels:
        content = message.content.lower()
        if any(word in content for word in bad_words):
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

# ====== CHAT (ECHO) ======
@bot.command()
async def chat(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

# ====== FORMAT ======
def format_lines(text):
    lines = text.split(";")
    return "\n".join(line.strip() for line in lines)

# ====== BÀI TẬP ======
@bot.command(name="bt")
async def baitap(ctx, date, so_mon: int, *, noidung):
    await ctx.message.delete()
    try:
        lines = noidung.split(";")

        if len(lines) != so_mon:
            return await ctx.send(f"❌ Bạn ghi {so_mon} môn nhưng nhập {len(lines)} dòng!")

        formatted = format_lines(noidung)

        embed = discord.Embed(
            title=f"📚 BÀI TẬP ({date})",
            description=formatted,
            color=0x00ffcc
        )
        embed.set_footer(text=f"Từ {ctx.author}")

        await ctx.send(embed=embed)

    except:
        await ctx.send("❌ Sai cú pháp!\n!bt 13/4/2026 3 Toán: bài 1; Văn: bài 2; Anh: bài 3")

# ====== BÁO BÀI ======
@bot.command(name="bb")
async def baobai(ctx, so_mon: int, *, noidung):
    await ctx.message.delete()
    try:
        lines = noidung.split(";")

        if len(lines) != so_mon:
            return await ctx.send(f"❌ Bạn ghi {so_mon} môn nhưng nhập {len(lines)} dòng!")

        formatted = format_lines(noidung)

        embed = discord.Embed(
            title="📢 BÁO BÀI",
            description=formatted,
            color=0xffcc00
        )
        embed.set_footer(text=f"Từ {ctx.author}")

        await ctx.send(embed=embed)

    except:
        await ctx.send("❌ Sai cú pháp!\n!bb 2 Toán: kiểm tra; Văn: nộp bài")

# ====== MODAL ======
class RenameModal(discord.ui.Modal, title="Đổi tên phòng"):
    new_name = discord.ui.TextInput(label="Tên mới", max_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel
        if not vc or voice_owners.get(vc.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await vc.edit(name=f"🎙️ {self.new_name.value}")
        await interaction.response.send_message("✅ Đã đổi tên", ephemeral=True)

class LimitModal(discord.ui.Modal, title="Giới hạn người"):
    limit = discord.ui.TextInput(label="Nhập số")

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel
        if not vc or voice_owners.get(vc.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        try:
            await vc.edit(user_limit=int(self.limit.value))
            await interaction.response.send_message("✅ Đã set limit", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Sai số", ephemeral=True)

# ====== VIEW ======
class VoiceControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_vc(self, interaction):
        return interaction.user.voice.channel if interaction.user.voice else None

    def is_owner(self, interaction, vc):
        return vc and voice_owners.get(vc.id) == interaction.user.id

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary)
    async def rename(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger)
    async def lock(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Đã khoá", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success)
    async def unlock(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        await vc.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Đã mở", ephemeral=True)

    @discord.ui.button(label="👥 Limit", style=discord.ButtonStyle.secondary)
    async def limit(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        await interaction.response.send_modal(LimitModal())

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction, _):
        vc = self.get_vc(interaction)
        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        await vc.delete()
        voice_owners.pop(vc.id, None)
        await interaction.response.send_message("🗑️ Đã xoá", ephemeral=True)

# ====== SEND UI ======
async def send_ui(channel):
    embed = discord.Embed(
        title="🎛️ Voice Control Panel",
        description="Điều khiển phòng voice",
        color=0x00ffcc
    )
    await channel.send(embed=embed, view=VoiceControlView())

# ====== READY ======
@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    bot.add_view(VoiceControlView())

# ====== VOICE ======
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    if after.channel and after.channel.name == VOICE_TRIGGER_NAME:
        vc = await guild.create_voice_channel(
            f"🎙️ {member.name}",
            category=after.channel.category
        )

        voice_owners[vc.id] = member.id
        await member.move_to(vc)

        text_channel = discord.utils.get(guild.text_channels, name=CONTROL_CHANNEL_NAME)
        if text_channel:
            await send_ui(text_channel)

    if before.channel and before.channel.name.startswith("🎙️") and len(before.channel.members) == 0:
        voice_owners.pop(before.channel.id, None)
        await before.channel.delete()

# ====== NR (DM MEMBER) ======
@bot.command(name="NR")
async def dm(ctx, member: discord.Member, *, message):
    await ctx.message.delete()

    try:
        await member.send(message)
        await ctx.send(f"📩 Đã gửi DM cho {member.mention}", delete_after=5)
    except:
        await ctx.send("❌ Không thể gửi tin nhắn", delete_after=5)

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
