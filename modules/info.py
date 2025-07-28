"""GPL-3.0 License"""
import os
import platform
import time

import disnake
from disnake.ext import commands

VERSION = os.getenv("VERSION", "Fail")

class InfoModule(commands.Cog):
    """Cog for providing information about the bot"""
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="help", description="Информация о боте")
    async def help(self, interaction: disnake.CommandInteraction):
        """Send a help message with available commands"""
        embed = disnake.Embed(
            title="Команды",
            description=(
                "``!close`` - для закрытия вопроса/ветки в форуме которым я управляю.",
                "\n\nДля админов выберите все слеш команды от меня."
            ),
            color=disnake.Color.purple(),
        )
        embed.set_footer(
            text="Made with ❤️ by PrivateKey",
            icon_url=self.bot.user.display_avatar.url,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="info", description="Информация о боте")
    async def info(self, interaction: disnake.CommandInteraction):
        """Send bot information including uptime, ping, and version"""
        uptime_seconds = int(time.time() - self.bot.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        ping = round(self.bot.latency * 1000)
        guild_count = len(self.bot.guilds)
        user_count = len(
            set(member.id for guild in self.bot.guilds for member in guild.members)
        )
        disnake_version = disnake.__version__
        python_version = platform.python_version()
        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

        embed_color = (
            disnake.Color.green()
            if ping < 100
            else disnake.Color.yellow() if ping < 250 else disnake.Color.red()
        )

        embed = disnake.Embed(
            title="Информация о боте",
            color=embed_color,
            timestamp=disnake.utils.utcnow(),
        )

        embed.add_field(name="📡 Пинг", value=f"`{ping} ms`", inline=True)
        embed.add_field(
            name="⏳ Аптайм", value=f"`{hours}h {minutes}m {seconds}s`", inline=True
        )
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="🛠️ Серверов", value=f"`{guild_count}`", inline=True)
        embed.add_field(name="👥 Пользователей", value=f"`{user_count}`", inline=True)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="📦 Disnake", value=f"`v{disnake_version}`", inline=True)
        embed.add_field(name="🐍 Python", value=f"`v{python_version}`", inline=True)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="💻 ОС", value=f"`{os_info}`", inline=False)

        embed.set_footer(
            text="Made with ❤️ by PrivateKey",
            icon_url=self.bot.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="about", description="Информация о боте")
    async def about(self, interaction: disnake.CommandInteraction):
        """Send bot information including version and author"""
        embed = disnake.Embed(
            title="О боте",
            description="Бот для управления вопросами в форумах для KDS.",
            color=disnake.Color.purple(),
        )
        embed.add_field(name="Версия", value=VERSION, inline=True)
        embed.set_footer(
            text="Made with ❤️ by PrivateKey",
            icon_url=self.bot.user.display_avatar.url,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    """Setup function to connect InfoModule"""
    bot.add_cog(InfoModule(bot))
