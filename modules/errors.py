# GPL-v3

import disnake
import uuid, traceback, datetime, os

from disnake.ext import commands


class NotOwner(commands.CheckFailure):
    pass


class ErrorsModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ### Triggers when an error occurs in a command ###

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        errEmbed = disnake.Embed(title="Ошибка", color=disnake.Color.red())
        user_avatar = (
            ctx.author.display_avatar.url
            if ctx.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        errEmbed.set_footer(text=f"{ctx.author.name}", icon_url=user_avatar)
        if isinstance(error, NotOwner):
            errEmbed.description = "Вы не разработчик бота."
            return await ctx.reply(embed=errEmbed, delete_after=40)

    ### Triggers when an error occurs in a slash command ###

    @commands.Cog.listener()
    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, error: Exception
    ):

        errEmbed = disnake.Embed(title="Ошибка", color=disnake.Color.red())
        user_avatar = (
            inter.author.display_avatar.url
            if inter.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        errEmbed.set_footer(text=f"{inter.author.name}", icon_url=user_avatar)

        if isinstance(error, commands.NoPrivateMessage):
            errEmbed.description = "Эта команда недоступна в личных сообщениях."
            return await inter.response.send_message(embed=errEmbed, ephemeral=True)

        if isinstance(error, disnake.Forbidden):
            errEmbed.description = "У меня нет прав для выполнения этого действия."
            return await inter.response.send_message(embed=errEmbed, ephemeral=True)

        if isinstance(error, commands.MissingPermissions):
            errEmbed.description = "У вас нет прав для использования этой команды."
            return await inter.response.send_message(embed=errEmbed, ephemeral=True)

        if isinstance(error, commands.CheckFailure):
            errEmbed.description = "Вы не можете использовать эту команду здесь."
            return await inter.response.send_message(embed=errEmbed, ephemeral=True)

        error_id = str(uuid.uuid4())[:8]
        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"error_{error_id}_{date_str}.log"

        os.makedirs("logs", exist_ok=True)
        full_path = os.path.join("logs", filename)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(f"=== Ошибка {error_id} ({date_str}) ===\n")
            f.write(f"Пользователь: {inter.author} (ID: {inter.author.id})\n")
            f.write(
                f"Гильдия: {inter.guild.name if inter.guild else 'DM'} (ID: {inter.guild.id if inter.guild else 'DM'})\n"
            )
            f.write(f"Команда: {inter.application_command.name}\n\n")
            traceback.print_exception(type(error), error, error.__traceback__, file=f)

        print(
            f"[ERROR] ID={error_id} | {type(error).__name__}: {error} (сохранено в {full_path})"
        )

        errEmbed.description = f"Произошла неизвестная ошибка.\nСообщите UUID разработчику.\n\nUUID: `{error_id}"
        try:
            await inter.response.send_message(embed=errEmbed, ephemeral=True)
        except disnake.InteractionResponded:
            await inter.followup.send(embed=errEmbed, ephemeral=True)


def setup(bot):
    bot.add_cog(ErrorsModule(bot))
