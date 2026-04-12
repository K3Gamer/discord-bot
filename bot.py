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

# ====== BÁO BÀI ======
@bot.command()
async def baobai(ctx, *, noidung):
    await ctx.send(f"📢 **BÁO BÀI** từ {ctx.author.mention}:\n{noidung}")

# ====== PRIVATE CHAT ======
@bot.command()
async def private(ctx):
    private_channels.add(ctx.channel.id)
    await ctx.send("🔒 Đã bật chế độ private (tắt lọc từ bậy)")

@bot.command()
async def unprivate(ctx):
    private_channels.discard(ctx.channel.id)
    await ctx.send("🔓 Đã tắt chế độ private")

# ====== FILTER BAD WORD ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # bỏ qua kênh private
    if message.channel.id not in private_channels:
        content = message.content.lower()
        if any(word in content for word in bad_words):
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention} nói bậy!")
            return

    await bot.process_commands(message)

# ====== MODAL ======
class RenameModal(discord.ui.Modal, title="Đổi tên phòng"):
    new_name = discord.ui.TextInput(label="Tên mới", max_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel
        if voice_owners.get(vc.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await vc.edit(name=f"🎙️ {self.new_name.value}")
        await interaction.response.send_message("✅ Đã đổi tên", ephemeral=True)

class LimitModal(discord.ui.Modal, title="Giới hạn người"):
    limit = discord.ui.TextInput(label="Nhập số")

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel

        if voice_owners.get(vc.id) != interaction.user.id:
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
        return voice_owners.get(vc.id) == interaction.user.id

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary)
    async def rename(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger)
    async def lock(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Đã khoá", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success)
    async def unlock(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        await vc.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Đã mở", ephemeral=True)

    @discord.ui.button(label="👥 Limit", style=discord.ButtonStyle.secondary)
    async def limit(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        await interaction.response.send_modal(LimitModal())

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
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

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
