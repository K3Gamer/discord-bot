import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_voice_channels = {}

# ====== VIEW BUTTON ======
class VoiceControlView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    def check_owner(self, interaction):
        return interaction.user.id == self.owner_id

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_owner(interaction):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await interaction.response.send_message("Nhập tên mới:", ephemeral=True)

        def check(m):
            return m.author == interaction.user

        msg = await bot.wait_for("message", check=check)
        vc = interaction.guild.get_channel(user_voice_channels.get(interaction.user.id))
        await vc.edit(name=f"🎙️ {msg.content}")
        await msg.delete()

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger)
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_owner(interaction):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        vc = interaction.guild.get_channel(user_voice_channels.get(interaction.user.id))
        await vc.set_permissions(interaction.guild.default_role, connect=False)

        await interaction.response.send_message("🔒 Đã khoá", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success)
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_owner(interaction):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        vc = interaction.guild.get_channel(user_voice_channels.get(interaction.user.id))
        await vc.set_permissions(interaction.guild.default_role, connect=True)

        await interaction.response.send_message("🔓 Đã mở", ephemeral=True)

    @discord.ui.button(label="➕ Add", style=discord.ButtonStyle.secondary)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_owner(interaction):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await interaction.response.send_message("Tag người cần thêm:", ephemeral=True)

        def check(m):
            return m.author == interaction.user

        msg = await bot.wait_for("message", check=check)
        if msg.mentions:
            member = msg.mentions[0]
            vc = interaction.guild.get_channel(user_voice_channels.get(interaction.user.id))
            await vc.set_permissions(member, connect=True, speak=True)

        await msg.delete()

    @discord.ui.button(label="🚫 Block", style=discord.ButtonStyle.secondary)
    async def block(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_owner(interaction):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        await interaction.response.send_message("Tag người cần block:", ephemeral=True)

        def check(m):
            return m.author == interaction.user

        msg = await bot.wait_for("message", check=check)
        if msg.mentions:
            member = msg.mentions[0]
            vc = interaction.guild.get_channel(user_voice_channels.get(interaction.user.id))
            await vc.set_permissions(member, connect=False)

        await msg.delete()

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.check_owner(interaction):
            return await interaction.response.send_message("❌ Không phải phòng của bạn", ephemeral=True)

        vc = interaction.guild.get_channel(user_voice_channels.get(interaction.user.id))
        await vc.delete()
        del user_voice_channels[interaction.user.id]

        await interaction.response.send_message("🗑️ Đã xoá phòng", ephemeral=True)


# ====== CREATE UI ======
async def create_ui(channel, owner_id):
    embed = discord.Embed(
        title="🎛️ Voice Control Panel",
        description="Dùng nút bên dưới để điều khiển phòng voice của bạn",
        color=0x00ffcc
    )
    await channel.send(embed=embed, view=VoiceControlView(owner_id))


# ====== READY ======
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

# ====== AUTO VOICE ======
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    trigger = "➕Nhấn để tạo Voice"

    # tạo phòng
    if after.channel and after.channel.name == trigger:
        vc = await guild.create_voice_channel(f"🎙️ {member.name}", category=after.channel.category)
        user_voice_channels[member.id] = vc.id
        await member.move_to(vc)

        # gửi UI vào channel text bất kỳ (chọn channel hiện tại đầu tiên)
        text_channel = discord.utils.get(guild.text_channels)
        await create_ui(text_channel, member.id)

    # xoá phòng khi rỗng
    if before.channel and before.channel.name.startswith("🎙️") and len(before.channel.members) == 0:
        cid = before.channel.id
        await before.channel.delete()

        for uid, vid in list(user_voice_channels.items()):
            if vid == cid:
                del user_voice_channels[uid]

# ====== RESET UI ======
@bot.command()
async def resetUIvoice(ctx):
    await ctx.message.delete()
    await ctx.channel.purge(limit=10)
    await create_ui(ctx.channel, ctx.author.id)

# ====== RUN ======
bot.run(os.getenv("DISCORD_TOKEN"))
