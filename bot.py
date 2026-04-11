import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# lưu owner của room
voice_owners = {}

# ====== MODAL RENAME ======
class RenameModal(discord.ui.Modal, title="Đổi tên phòng"):
    new_name = discord.ui.TextInput(
        label="Tên mới",
        placeholder="Nhập tên phòng...",
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.user.voice.channel if interaction.user.voice else None

        if not vc:
            return await interaction.response.send_message("❌ Bạn không ở trong phòng", ephemeral=True)

        if voice_owners.get(vc.id) != interaction.user.id:
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await vc.edit(name=f"🎙️ {self.new_name.value}")
        await interaction.response.send_message("✅ Đã đổi tên", ephemeral=True)

# ====== VIEW ======
class VoiceControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_vc(self, interaction):
        return interaction.user.voice.channel if interaction.user.voice else None

    def is_owner(self, interaction, vc):
        return voice_owners.get(vc.id) == interaction.user.id

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_vc(interaction)

        if not vc:
            return await interaction.response.send_message("❌ Bạn chưa vào voice", ephemeral=True)

        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger)
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_vc(interaction)

        if not vc:
            return await interaction.response.send_message("❌ Bạn chưa vào voice", ephemeral=True)

        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Đã khoá", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success)
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_vc(interaction)

        if not vc:
            return await interaction.response.send_message("❌ Bạn chưa vào voice", ephemeral=True)

        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await vc.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Đã mở", ephemeral=True)

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_vc(interaction)

        if not vc:
            return await interaction.response.send_message("❌ Bạn chưa vào voice", ephemeral=True)

        if not self.is_owner(interaction, vc):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await vc.delete()
        voice_owners.pop(vc.id, None)

        await interaction.response.send_message("🗑️ Đã xoá phòng", ephemeral=True)

# ====== UI SEND ======
async def send_ui(channel):
    embed = discord.Embed(
        title="🎛️ Voice Control Panel",
        description="Dùng nút bên dưới để điều khiển phòng voice",
        color=0x00ffcc
    )
    await channel.send(embed=embed, view=VoiceControlView())

# ====== READY ======
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    bot.add_view(VoiceControlView())  # giữ button sau restart

# ====== AUTO CREATE ======
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    trigger = "➕Nhấn để tạo Voice"

    # tạo phòng
    if after.channel and after.channel.name == trigger:
        vc = await guild.create_voice_channel(f"🎙️ {member.name}", category=after.channel.category)
        voice_owners[vc.id] = member.id
        await member.move_to(vc)

        # gửi UI vào text channel đầu tiên
        text_channel = guild.text_channels[0]
        await send_ui(text_channel)

    # auto delete
    if before.channel and before.channel.name.startswith("🎙️") and len(before.channel.members) == 0:
        voice_owners.pop(before.channel.id, None)
        await before.channel.delete()

# ====== CHAT (ECHO) ======
@bot.command()
async def chat(ctx, *, message):
    await ctx.message.delete()  # xoá tin nhắn chứa !chat
    await ctx.send(message)     # gửi lại nội dung

# ====== RESET UI ======
@bot.command()
async def resetUIvoice(ctx):
    await ctx.message.delete()
    await ctx.channel.purge(limit=10)
    await send_ui(ctx.channel)

# ====== WELCOME DM ======
@bot.event
async def on_member_join(member):
    try:
        await member.send(
            f"🎉 Chào mừng {member.name} đến với nhóm **Bới Cái Đào**!\n\n"
            "👉 Hãy đọc kênh 🧭điều-hướng-nhanh🧭 để biết cách sử dụng server nhé!\n"
            "Chúc bạn có trải nghiệm vui vẻ 😄"
        )
    except:
        print(f"Không thể gửi DM cho {member.name}")

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
