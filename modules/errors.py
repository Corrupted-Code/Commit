"""GPL-3.0 License"""

import uuid
import traceback
import datetime
import os

import disnake

from disnake.ext import commands


class NotOwner(commands.CheckFailure):
    """Exception raised when a user is not the bot owner."""
    def __init__(self, message: str = "You are not the bot owner."):
        super().__init__(message)


class ErrorsModule(commands.Cog):
    """Cog for handling errors in commands and interactions."""
    def __init__(self, bot):
        self.bot = bot

    ### Triggers when an error occurs in a command ###

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: Exception
    ) -> None:
        """Handles errors in commands."""

        err_embed = self.bot.bot_embed(ctx)
        if isinstance(error, NotOwner):

            err_embed.description = "Вы не разработчик бота."
            return await ctx.reply(embed=err_embed, delete_after=40)

    ### Triggers when an error occurs in a slash command ###

    @commands.Cog.listener()
    async def on_slash_command_error(
        self: any, inter: disnake.ApplicationCommandInteraction, error: Exception
    ) -> None:
        """Handles errors in slash commands."""

        err_embed = self.bot.bot_embed(inter)

        if isinstance(error, commands.NoPrivateMessage):
            err_embed.description = "Эта команда недоступна в личных сообщениях."
            return await inter.response.send_message(embed=err_embed, ephemeral=True)

        if isinstance(error, disnake.Forbidden):
            err_embed.description = "У меня нет прав для выполнения этого действия."
            return await inter.response.send_message(embed=err_embed, ephemeral=True)

        if isinstance(error, commands.MissingPermissions):
            err_embed.description = "У вас нет прав для использования этой команды."
            return await inter.response.send_message(embed=err_embed, ephemeral=True)

        if isinstance(error, commands.CheckFailure):
            err_embed.description = "Вы не можете использовать эту команду здесь."
            return await inter.response.send_message(embed=err_embed, ephemeral=True)

        error_id = str(uuid.uuid4())[:8]
        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"error_{error_id}_{date_str}.log"

        os.makedirs("logs", exist_ok=True)
        full_path = os.path.join("logs", filename)

        def ifdm(inter):
            return inter.guild.name if inter.guild else 'DM'

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(f"=== Ошибка {error_id} ({date_str}) ===\n")
            f.write(f"Пользователь: {inter.author} (ID: {inter.author.id})\n")
            f.write(
                f"Гильдия: {ifdm(inter)} (ID: {ifdm(inter)})\n"
            )
            f.write(f"Команда: {inter.application_command.name}\n\n")
            traceback.print_exception(type(error), error, error.__traceback__, file=f)

        print(
            f"[ERROR] ID={error_id} | {type(error).__name__}: {error} (сохранено в {full_path})"
        )

        err_embed.description = (
            f"Произошла неизвестная ошибка.\n"
            f"Сообщите UUID разработчику.\n\n"
            f"UUID: `{error_id}"
        )
        try:
            await inter.response.send_message(embed=err_embed, ephemeral=True)
        except disnake.InteractionResponded:
            await inter.followup.send(embed=err_embed, ephemeral=True)


def setup(bot):
    """Setup function to connect ErrorsModule"""
    bot.add_cog(ErrorsModule(bot))
