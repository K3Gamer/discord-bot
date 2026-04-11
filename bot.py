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

# ====== MODAL RENAME ======
class RenameModal(discord.ui.Modal, title="Đổi tên phòng"):
    new_name = discord.ui.TextInput(label="Tên mới", max_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel
        if voice_owners.get(vc.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await vc.edit(name=f"🎙️ {self.new_name.value}")
        await interaction.response.send_message("✅ Đã đổi tên", ephemeral=True)

# ====== MODAL LIMIT ======
class LimitModal(discord.ui.Modal, title="Giới hạn người"):
    limit = discord.ui.TextInput(label="Nhập số (0 = không giới hạn)")

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel

        if voice_owners.get(vc.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        try:
            limit = int(self.limit.value)
            await vc.edit(user_limit=limit)
            await interaction.response.send_message(f"👥 Limit = {limit}", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Nhập số hợp lệ", ephemeral=True)

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

    @discord.ui.button(label="👢 Kick", style=discord.ButtonStyle.secondary)
    async def kick(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        members = [m for m in vc.members if m != interaction.user]
        if not members:
            return await interaction.response.send_message("❌ Không có ai để kick", ephemeral=True)

        await members[0].move_to(None)
        await interaction.response.send_message(f"👢 Đã kick {members[0].name}", ephemeral=True)

    @discord.ui.button(label="🔇 Mute", style=discord.ButtonStyle.secondary)
    async def mute(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        for m in vc.members:
            if m != interaction.user:
                await m.edit(mute=True)

        await interaction.response.send_message("🔇 Đã mute", ephemeral=True)

    @discord.ui.button(label="🔊 Unmute", style=discord.ButtonStyle.secondary)
    async def unmute(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        for m in vc.members:
            await m.edit(mute=False)

        await interaction.response.send_message("🔊 Đã unmute", ephemeral=True)

    @discord.ui.button(label="👑 Transfer", style=discord.ButtonStyle.primary)
    async def transfer(self, interaction, _):
        vc = self.get_vc(interaction)
        if not vc or not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không hợp lệ", ephemeral=True)

        members = [m for m in vc.members if m != interaction.user]
        if not members:
            return await interaction.response.send_message("❌ Không có ai", ephemeral=True)

        voice_owners[vc.id] = members[0].id
        await interaction.response.send_message(f"👑 Owner mới: {members[0].name}", ephemeral=True)

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
        description="Điều khiển phòng voice của bạn",
        color=0x00ffcc
    )
    await channel.send(embed=embed, view=VoiceControlView())

# ====== READY ======
@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    bot.add_view(VoiceControlView())

# ====== VOICE EVENT ======
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
