"""GPL-3.0 License"""

import disnake

from disnake.ext import commands


class ForumsModule(commands.Cog):
    """Cog for managing forums and threads in Discord"""
    def __init__(self, bot):
        self.bot = bot

    ## Prefix commands ##

    @commands.command(name="close")
    async def close_thread(self, ctx: commands.Context):
        """Close a thread in a forum channel"""
        err_embed = self.bot.bot_embed(ctx)

        if not isinstance(ctx.channel, disnake.Thread):
            err_embed.description = "Эта команда работает только в ветках."
            return await ctx.send(embed=err_embed, delete_after=40)

        data = self.bot.load_data()
        sid = str(ctx.guild.id)
        if (
            sid not in data
            or "forumchannels" not in data[sid]
            or str(ctx.channel.parent_id)
            not in [str(f) for f in data[sid]["forumchannels"]]
        ):
            err_embed.description = "Невозможно продолжить тут."
            return await ctx.send(embed=err_embed, delete_after=40)

        thread = ctx.channel
        if ctx.author.guild_permissions.manage_channels:
            if thread.archived or thread.locked:
                return False
            await thread.edit(archived=True, locked=True)
            await self.bot.send_close_embed(thread, ctx.author, "модератор")
        elif ctx.author.id == thread.owner_id:
            if thread.archived or thread.locked:
                return False
            await thread.edit(archived=True, locked=True)
            await self.bot.send_close_embed(thread, ctx.author, "автор")
        else:
            err_embed.description = "У вас нет прав закрывать эту ветку."
            await ctx.send(embed=err_embed, delete_after=40)

    @commands.slash_command(
        name="forum",
        description="Управление форумами",
        default_member_permissions=disnake.Permissions(manage_channels=True),
    )
    async def forum(self, _: disnake.CommandInteraction):
        """Base command for forum management"""
        return

    @forum.sub_command(name="add", description="Создать новый форум")
    async def forum_add(
        self,
        interaction: disnake.CommandInteraction,
        name: str = commands.Param(description="Название форума"),
    ):
        """Create a new forum channel"""
        if isinstance(interaction.channel, disnake.DMChannel):
            err_embed = self.bot.bot_embed(interaction)
            err_embed.description = "Эта команда недоступна в личных сообщениях."
            return await interaction.response.send_message(
                embed=err_embed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        forum = await interaction.guild.create_forum_channel(name)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)
        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": 1,
                "welcomeMessage": (
                    "Hello! {thread_author}, welcome to your thread "
                    "{thread_id} - {thread_name}"
                ),
            }
        data[sid]["forumchannels"].append(forum.id)
        self.bot.save_data(data)

        resp_embed = self.bot.bot_embed(interaction)
        resp_embed.title = "Форум создан"
        resp_embed.description = f"Форум **{name}** (ID: `{forum.id}`) создан."
        resp_embed.color = disnake.Color.purple()

        await interaction.edit_original_message(embed=resp_embed)

    @forum.sub_command(name="rem", description="Удалить форум")
    async def forum_rem(
        self,
        interaction: disnake.CommandInteraction,
        forum: str = commands.Param(description="Удаляемый форум", autocomplete=True),
    ):
        """Remove a forum channel"""
        if isinstance(interaction.channel, disnake.DMChannel):
            err_embed = self.bot.bot_embed(interaction)
            err_embed.description = "Эта команда недоступна в личных сообщениях."

            return await interaction.response.send_message(
                embed=err_embed, ephemeral=True
            )

        err_embed = self.bot.bot_embed(interaction)

        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)
        if sid not in data or not data[sid]["forumchannels"]:
            err_embed.description = "Форум-каналы не найдены."
            await interaction.edit_original_message(embed=err_embed)
            return

        try:
            fid = int(forum.split(" - ")[-1])
        except ValueError:
            err_embed.description = "Некорректный формат форума."
            await interaction.edit_original_message(embed=err_embed)
            return

        channel = interaction.guild.get_channel(fid)
        if not channel:
            err_embed.description = "Форум не найден."
            await interaction.edit_original_message(embed=err_embed)
            return

        await channel.delete()
        data[sid]["forumchannels"].remove(fid)
        self.bot.save_data(data)

        resp_embed = self.bot.bot_embed(interaction)
        resp_embed.title = "Форум удалён"
        resp_embed.description = f"Форум **{channel.name}** (ID: `{fid}`) был успешно удалён."
        resp_embed.color = disnake.Color.purple()

        author_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        resp_embed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
        await interaction.edit_original_message(embed=resp_embed)

    @forum.sub_command(
        name="toggle_message",
        description="Включить или выключить приветственное сообщение",
    )
    async def forum_welcome_toggle(
        self,
        interaction: disnake.CommandInteraction,
        value: bool = commands.Param(description="True - включить, False - выключить"),
    ):
        """Enable or disable the welcome message for threads"""
        if isinstance(interaction.channel, disnake.DMChannel):
            err_embed = self.bot.bot_embed(interaction)
            err_embed.description = "Эта команда недоступна в личных сообщениях."

            return await interaction.response.send_message(
                embed=err_embed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)

        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": 1,
                "welcomeMessage": (
                    "Hello! {thread_author}, welcome to your thread "
                    "{thread_id} - {thread_name}"
                ),
                "delete_closed": False,
                "welcome_enabled": value,
            }
        else:
            data[sid]["welcome_enabled"] = value

        self.bot.save_data(data)
        state = "включено" if value else "выключено"

        resp_embed = self.bot.bot_embed(interaction)
        resp_embed.title = "Настройки обновлены"
        resp_embed.description = f"Приветственное сообщение теперь **{state}**."
        resp_embed.color = disnake.Color.purple()

        await interaction.edit_original_message(embed=resp_embed)

    @forum.sub_command(
        name="close_after", description="Установить время закрытия до ветки"
    )
    async def close_after(
        self,
        interaction: disnake.CommandInteraction,
        hours: int = commands.Param(description="Время в часах."),
    ):
        """Set the time after which threads will be closed automatically"""
        if isinstance(interaction.channel, disnake.DMChannel):
            err_embed = self.bot.bot_embed(interaction)
            err_embed.description = "Эта команда недоступна в личных сообщениях."

            return await interaction.response.send_message(
                embed=err_embed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)
        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": hours,
                "welcomeMessage": (
                    "Hello! {thread_author}, welcome to your thread ",
                    "{thread_id} - {thread_name}"
                ),
            }
        else:
            data[sid]["closeAfter"] = hours
        self.bot.save_data(data)

        resp_embed = self.bot.bot_embed(interaction)
        resp_embed.title = "Настройки форума обновлены"
        resp_embed.description = f"Ветки автоматически закрываются после: {hours} часов инактива."
        resp_embed.color = disnake.Color.purple()

        await interaction.edit_original_message(embed=resp_embed)

    @forum.sub_command(
        name="message", description="Установить приветственное сообщение"
    )
    async def forum_welcome_message(self, interaction: disnake.CommandInteraction):
        """Set the welcome message for new threads"""

        bot = self.bot
        if isinstance(interaction.channel, disnake.DMChannel):
            err_embed = self.bot.bot_embed(interaction)
            err_embed.description = "Эта команда недоступна в личных сообщениях."

            return await interaction.response.send_message(
                embed=err_embed, ephemeral=True
            )
        class WelcomeModal(disnake.ui.Modal):
            """Modal for setting welcome message"""
            def __init__(self):
                self.bot = bot
                components = [
                    disnake.ui.TextInput(
                        label="Приветственное сообщение",
                        placeholder=(
                            "Hello! {thread_author}, welcome to your thread "
                            "{thread_id} - {thread_name}"
                        ),
                        custom_id="welcome_msg",
                        style=disnake.TextInputStyle.paragraph,
                        max_length=200,
                    )
                ]
                super().__init__(title="Настройка приветствия", components=components)

            async def callback(self, interaction: disnake.ModalInteraction):
                msg = interaction.text_values["welcome_msg"]
                data = self.bot.load_data()
                sid = str(interaction.guild.id)
                if sid not in data:
                    data[sid] = {
                        "forumchannels": [],
                        "closeAfter": 1,
                        "welcomeMessage": msg,
                    }
                else:
                    data[sid]["welcomeMessage"] = msg
                self.bot.save_data(data)

                resp_embed = self.bot.bot_embed(interaction)
                resp_embed.title = "Приветственное сообщение обновлено"
                resp_embed.description = f"Приветственное сообщение:\n```{msg}```"
                resp_embed.color = disnake.Color.purple()

                await interaction.response.send_message(embed=resp_embed, ephemeral=True)


        await interaction.response.send_modal(modal=WelcomeModal())

    @forum.sub_command(
        name="deleteclosed",
        description="Включить/выключить кнопку удаления закрытых веток",
    )
    async def forum_delete_closed(
        self,
        interaction: disnake.CommandInteraction,
        value: bool = commands.Param(description="True или False"),
    ):
        """Enable or disable the delete closed threads button"""
        if isinstance(interaction.channel, disnake.DMChannel):
            err_embed = self.bot.bot_embed(interaction)
            err_embed.description = "Эта команда недоступна в личных сообщениях."
            return await interaction.response.send_message(
                embed=err_embed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        servid = str(interaction.guild.id)
        if servid not in data:
            data[servid] = {
                "forumchannels": [],
                "closeAfter": 1,
                "welcomeMessage": (
                    "Hello! {thread_author}, welcome to your thread ",
                    "{thread_id} - {thread_name}"
                ),
                "delete_closed": value,
            }
        else:
            data[servid]["delete_closed"] = value
        self.bot.save_data(data)
        if value:
            value = "включено"
        else:
            value = "выключено"


        resp_embed = self.bot.bot_embed(interaction)
        resp_embed.title = "Настройки обновлены"
        resp_embed.description = f"Автоудаление закрытых веток теперь **{value}**."
        resp_embed.color = disnake.Color.purple()
        await interaction.edit_original_message(embed=resp_embed)

    @forum_rem.autocomplete("forum")
    async def removeforum_autocomplete(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        """Autocomplete for forum removal command"""
        if isinstance(inter.channel, disnake.DMChannel):
            return

        data = self.bot.load_data()
        sid = str(inter.guild.id)
        results = []
        if sid in data and data[sid]["forumchannels"]:
            for fid in data[sid]["forumchannels"]:
                channel = inter.guild.get_channel(fid)
                if channel:
                    label = f"{channel.name} - {fid}"
                    if user_input.lower() in label.lower():
                        results.append(label)
        return results[:25]


def setup(bot):
    """Load the ForumsModule cog"""
    bot.add_cog(ForumsModule(bot))
