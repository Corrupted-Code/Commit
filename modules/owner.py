"""GPL-3.0 License"""

import asyncio
import os
import subprocess
import sys

import disnake
from disnake.ext import commands
from disnake.ui import Button, View

from modules import errors as em

OWNER_IDS = [int(i) for i in os.getenv("OWNER_IDS", "").replace(" ", "").split(",") if i]

def is_bot_owner():
    """Check if the user is the bot owner."""
    def predicate(ctx):
        if ctx.author.id not in OWNER_IDS:
            raise em.NotOwner("Вы не разработчик бота.")
        return True

    return commands.check(predicate)

class OwnerModule(commands.Cog):
    """Cog for bot owner commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_bot_owner()
    async def reboot(self, ctx):
        """Reboot command for bot owner"""
        bot = self.bot
        err_embed = bot.bot_embed(ctx)

        class ConfirmView(View):
            """View for confirmation buttons"""
            def __init__(self):
                super().__init__(timeout=30)

            @disnake.ui.button(label="Да", style=disnake.ButtonStyle.green)
            # @is_bot_owner()
            # ### Нельзя это цеплять на кнопки, т.к. я не видел листенера для ошибок кнопок ###
            async def yes(
                self, _: Button, interaction: disnake.MessageInteraction
            ):
                """Yes button handler"""
                if interaction.author.id not in OWNER_IDS:
                    err_embed.description = (
                        "У вас нет прав на выполнение этого действия."
                    )
                    return await interaction.response.send_message(
                        embed=err_embed, ephemeral=True
                    )
                err_embed.title = "Перезагрузка..."
                await interaction.response.edit_message(embed=err_embed, view=None)

                print("DEBUG: Был вызван перезапуск")

                await bot.change_presence(
                    activity=disnake.Activity(
                        type=disnake.ActivityType.watching, name="перезапуск"
                    )
                )
                if os.path.exists(".git"):
                    try:
                        subprocess.run(["git", "pull"], check=True)
                        print("DEBUG: Автообновление успешно.")
                    except subprocess.CalledProcessError as e:
                        print(f"DEBUG: Ошибка: {e}")

                await asyncio.sleep(3)
                print("DEBUG: Запуск бота...")
                os.execv(sys.executable, [sys.executable] + sys.argv)

            @disnake.ui.button(label="Нет", style=disnake.ButtonStyle.red)
            # @is_bot_owner()
            # ### Нельзя это цеплять на кнопки, т.к. я не видел листенера для ошибок кнопок ###
            async def no(self, _: Button, interaction: disnake.MessageInteraction):
                """No button handler"""
                if interaction.author.id not in OWNER_IDS:
                    err_embed.description = (
                        "У вас нет прав на выполнение этого действия."
                    )
                    return await interaction.response.send_message(
                        embed=err_embed, ephemeral=True
                    )

                await interaction.message.delete()
                try:
                    await ctx.message.delete()
                except (disnake.Forbidden, disnake.HTTPException, disnake.NotFound):
                    pass

            async def on_timeout(self):
                try:
                    err_embed.title = "⏳ Время ожидания истекло."
                    await message.edit(embed=err_embed, view=None)
                except (disnake.Forbidden, disnake.HTTPException, disnake.NotFound):
                    pass

        resp_embed = self.bot.bot_embed(ctx)
        resp_embed.title = "Подтверждение перезагрузки"
        resp_embed.description = "Вы уверены что хотите перезапустить бота?"
        resp_embed.color = disnake.Color.orange()

        message = await ctx.send(embed=resp_embed, view=ConfirmView())


def setup(bot):
    """Setup function to connect OwnerModule """
    bot.add_cog(OwnerModule(bot))
