# GPL-v3

import disnake
import sys, subprocess, os, asyncio
from disnake.ext import commands
from disnake.ui import View, Button

from modules import errors as em
from config import OWNER_IDS

### Check if user is bot owner ###


def is_bot_owner():
    def predicate(ctx):
        if ctx.author.id not in OWNER_IDS:
            raise em.NotOwner("Вы не разработчик бота.")
        return True

    return commands.check(predicate)


class OwnerModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ### Reboot command for bot owner ###

    @commands.command()
    @is_bot_owner()
    async def reboot(self, ctx):
        bot = self.bot
        errEmbed = disnake.Embed(title="Ошибка", color=disnake.Color.red())
        user_avatar = (
            ctx.author.display_avatar.url
            if ctx.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        errEmbed.set_footer(text=f"{ctx.author.name}", icon_url=user_avatar)

        if ctx.author.id not in OWNER_IDS:
            errEmbed.description = "У вас нет прав на перезагрузку бота."
            return await ctx.send(embed=errEmbed, delete_after=10)

        confirmEmbed = disnake.Embed(
            title="Вы уверены что хотите перезапустить бота?",
            color=disnake.Color.orange(),
        )
        confirmEmbed.set_footer(text=f"{ctx.author.name}", icon_url=user_avatar)

        class ConfirmView(View):
            def __init__(self):
                super().__init__(timeout=30)

            @disnake.ui.button(label="Да", style=disnake.ButtonStyle.green)
            # @is_bot_owner() ### Нельзя это цеплять на кнопки, т.к. я не видел листенера для ошибок кнопок ###
            async def yes(
                self, button: Button, interaction: disnake.MessageInteraction
            ):
                if interaction.author.id not in OWNER_IDS:
                    errEmbed.description = (
                        "У вас нет прав на выполнение этого действия."
                    )
                    return await interaction.response.send_message(
                        embed=errEmbed, ephemeral=True
                    )
                errEmbed.title = "Перезагрузка..."
                await interaction.response.edit_message(embed=errEmbed, view=None)

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
            # @is_bot_owner() ### Нельзя это цеплять на кнопки, т.к. я не видел листенера для ошибок кнопок ###
            async def no(self, button: Button, interaction: disnake.MessageInteraction):
                if interaction.author.id not in OWNER_IDS:
                    errEmbed.description = (
                        "У вас нет прав на выполнение этого действия."
                    )
                    return await interaction.response.send_message(
                        embed=errEmbed, ephemeral=True
                    )

                await interaction.message.delete()
                try:
                    await ctx.message.delete()
                except:
                    pass

            async def on_timeout(self):
                try:
                    errEmbed.title = "⏳ Время ожидания истекло."
                    await message.edit(embed=errEmbed, view=None)
                except:
                    pass

        message = await ctx.send(embed=confirmEmbed, view=ConfirmView())


def setup(bot):
    bot.add_cog(OwnerModule(bot))
