# GPL-v3

import disnake

from disnake.ext import commands


class ForumsModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ## Prefix commands ##

    @commands.command(name="close")
    async def close_thread(self, ctx: commands.Context):
        errEmbed = disnake.Embed(
            title="Упс!",
            color=disnake.Color.red(),
        )
        author_avatar = (
            ctx.author.display_avatar.url
            if ctx.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        errEmbed.set_footer(text=f"{ctx.author.name}", icon_url=author_avatar)

        if not isinstance(ctx.channel, disnake.Thread):
            errEmbed.description = "Эта команда работает только в ветках."
            return await ctx.send(embed=errEmbed, delete_after=40)

        data = self.bot.load_data()
        sid = str(ctx.guild.id)
        if (
            sid not in data
            or "forumchannels" not in data[sid]
            or str(ctx.channel.parent_id)
            not in [str(f) for f in data[sid]["forumchannels"]]
        ):
            errEmbed.description = "Невозможно продолжить тут."
            return await ctx.send(embed=errEmbed, delete_after=40)

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
            errEmbed.description = "У вас нет прав закрывать эту ветку."
            await ctx.send(embed=errEmbed, delete_after=40)

    ## Slash commands ##

    @commands.slash_command(
        name="forum",
        description="Управление форумами",
        default_member_permissions=disnake.Permissions(manage_channels=True),
    )
    async def forum(self, interaction: disnake.CommandInteraction):
        pass

    ### Add new forum command ###

    @forum.sub_command(name="add", description="Создать новый форум")
    async def forum_add(
        self,
        interaction: disnake.CommandInteraction,
        name: str = commands.Param(description="Название форума"),
    ):
        if isinstance(interaction.channel, disnake.DMChannel):
            errEmbed = disnake.Embed(
                title="Ошибка",
                description="Эта команда недоступна в личных сообщениях.",
                color=disnake.Color.red(),
            )
            user_avatar = (
                interaction.author.display_avatar.url
                if interaction.author.display_avatar
                else self.bot.user.display_avatar.url
            )
            errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=user_avatar)
            return await interaction.response.send_message(
                embed=errEmbed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        forum = await interaction.guild.create_forum_channel(name)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)
        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": 1,
                "welcomeMessage": "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
            }
        data[sid]["forumchannels"].append(forum.id)
        self.bot.save_data(data)
        respEmbed = disnake.Embed(
            title="Форум создан",
            description=f"Форум **{name}** (ID: `{forum.id}`) создан.",
            color=disnake.Color.purple(),
        )
        author_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
        await interaction.edit_original_message(embed=respEmbed)

    ### Remove forum command ###

    @forum.sub_command(name="rem", description="Удалить форум")
    async def forum_rem(
        self,
        interaction: disnake.CommandInteraction,
        forum: str = commands.Param(description="Удаляемый форум", autocomplete=True),
    ):
        if isinstance(interaction.channel, disnake.DMChannel):
            errEmbed = disnake.Embed(
                title="Ошибка",
                description="Эта команда недоступна в личных сообщениях.",
                color=disnake.Color.red(),
            )
            user_avatar = (
                interaction.author.display_avatar.url
                if interaction.author.display_avatar
                else self.bot.user.display_avatar.url
            )
            errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=user_avatar)
            return await interaction.response.send_message(
                embed=errEmbed, ephemeral=True
            )

        errEmbed = disnake.Embed(
            title="Упс!",
            color=disnake.Color.red(),
        )
        author_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)
        if sid not in data or not data[sid]["forumchannels"]:
            errEmbed.description = "Форум-каналы не найдены."
            await interaction.edit_original_message(embed=errEmbed)
            return

        try:
            fid = int(forum.split(" - ")[-1])
        except Exception:
            errEmbed.description = "Некорректный формат форума."
            await interaction.edit_original_message(embed=errEmbed)
            return

        channel = interaction.guild.get_channel(fid)
        if not channel:
            errEmbed.description = "Форум не найден."
            await interaction.edit_original_message(embed=errEmbed)
            return

        await channel.delete()
        data[sid]["forumchannels"].remove(fid)
        self.bot.save_data(data)

        respEmbed = disnake.Embed(
            title="Форум удалён",
            description=f"Форум **{channel.name}** (ID: `{fid}`) был успешно удалён.",
            color=disnake.Color.purple(),
        )
        author_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
        await interaction.edit_original_message(embed=respEmbed)

    ### Toggle welcome message ###

    @forum.sub_command(
        name="toggle_message",
        description="Включить или выключить приветственное сообщение",
    )
    async def forum_welcome_toggle(
        self,
        interaction: disnake.CommandInteraction,
        value: bool = commands.Param(description="True - включить, False - выключить"),
    ):
        if isinstance(interaction.channel, disnake.DMChannel):
            errEmbed = disnake.Embed(
                title="Ошибка",
                description="Эта команда недоступна в личных сообщениях.",
                color=disnake.Color.red(),
            )
            user_avatar = (
                interaction.author.display_avatar.url
                if interaction.author.display_avatar
                else self.bot.user.display_avatar.url
            )
            errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=user_avatar)
            return await interaction.response.send_message(
                embed=errEmbed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)

        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": 1,
                "welcomeMessage": "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
                "delete_closed": False,
                "welcome_enabled": value,
            }
        else:
            data[sid]["welcome_enabled"] = value

        self.bot.save_data(data)
        state = "включено" if value else "выключено"

        respEmbed = disnake.Embed(
            title="Настройки обновлены",
            description=f"Приветственное сообщение теперь **{state}**.",
            color=disnake.Color.purple(),
        )
        author_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
        await interaction.edit_original_message(embed=respEmbed)

    ### Close after setting ###

    @forum.sub_command(
        name="close_after", description="Установить время закрытия до ветки"
    )
    async def close_after(
        self,
        interaction: disnake.CommandInteraction,
        hours: int = commands.Param(description="Время в часах."),
    ):
        if isinstance(interaction.channel, disnake.DMChannel):
            errEmbed = disnake.Embed(
                title="Ошибка",
                description="Эта команда недоступна в личных сообщениях.",
                color=disnake.Color.red(),
            )
            user_avatar = (
                interaction.author.display_avatar.url
                if interaction.author.display_avatar
                else self.bot.user.display_avatar.url
            )
            errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=user_avatar)
            return await interaction.response.send_message(
                embed=errEmbed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)
        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": hours,
                "welcomeMessage": "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
            }
        else:
            data[sid]["closeAfter"] = hours
        self.bot.save_data(data)
        respEmbed = disnake.Embed(
            title="Настройки форума обновлены",
            description=f"Ветки автоматически закрываются после: {hours} часов инактива.",
            color=disnake.Color.purple(),
        )
        author_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
        await interaction.edit_original_message(embed=respEmbed)

    ### Welcome message setting ###

    @forum.sub_command(
        name="message", description="Установить приветственное сообщение"
    )
    async def forum_welcome_message(self, interaction: disnake.CommandInteraction):
        if isinstance(interaction.channel, disnake.DMChannel):
            errEmbed = disnake.Embed(
                title="Ошибка",
                description="Эта команда недоступна в личных сообщениях.",
                color=disnake.Color.red(),
            )
            user_avatar = (
                interaction.author.display_avatar.url
                if interaction.author.display_avatar
                else self.bot.user.display_avatar.url
            )
            errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=user_avatar)
            return await interaction.response.send_message(
                embed=errEmbed, ephemeral=True
            )

        class WelcomeModal(disnake.ui.Modal):
            def __init__(self):
                components = [
                    disnake.ui.TextInput(
                        label="Приветственное сообщение",
                        placeholder="Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
                        custom_id="welcome_msg",
                        style=disnake.TextInputStyle.paragraph,
                        max_length=200,
                    )
                ]
                super().__init__(title="Настройка приветствия", components=components)

            async def callback(self, modal_inter: disnake.ModalInteraction):
                msg = modal_inter.text_values["welcome_msg"]
                data = self.bot.load_data()
                sid = str(modal_inter.guild.id)
                if sid not in data:
                    data[sid] = {
                        "forumchannels": [],
                        "closeAfter": 1,
                        "welcomeMessage": msg,
                    }
                else:
                    data[sid]["welcomeMessage"] = msg
                self.bot.save_data(data)
                respEmbed = disnake.Embed(
                    title="Настройки обновлены",
                    description=f"Приветственное сообщение:\n```{msg}```",
                    color=disnake.Color.purple(),
                )
                author_avatar = (
                    interaction.author.display_avatar.url
                    if interaction.author.display_avatar
                    else self.bot.user.display_avatar.url
                )
                errEmbed.set_footer(
                    text=f"{interaction.author.name}", icon_url=author_avatar
                )
                await modal_inter.response.send_message(embed=respEmbed, ephemeral=True)

        await interaction.response.send_modal(modal=WelcomeModal())

    ### Delete closed threads setting ###

    @forum.sub_command(
        name="deleteclosed",
        description="Включить/выключить кнопку удаления закрытых веток",
    )
    async def forum_delete_closed(
        self,
        interaction: disnake.CommandInteraction,
        value: bool = commands.Param(description="True или False"),
    ):
        if isinstance(interaction.channel, disnake.DMChannel):
            errEmbed = disnake.Embed(
                title="Ошибка",
                description="Эта команда недоступна в личных сообщениях.",
                color=disnake.Color.red(),
            )
            user_avatar = (
                interaction.author.display_avatar.url
                if interaction.author.display_avatar
                else self.bot.user.display_avatar.url
            )
            errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=user_avatar)
            return await interaction.response.send_message(
                embed=errEmbed, ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        data = self.bot.load_data()
        sid = str(interaction.guild.id)
        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": 1,
                "welcomeMessage": "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
                "delete_closed": value,
            }
        else:
            data[sid]["delete_closed"] = value
        self.bot.save_data(data)
        if value:
            value = "включено"
        else:
            value = "выключено"

        respEmbed = disnake.Embed(
            title="Настройки обновлены",
            description=f"Автоудаление закрытых веток теперь **{value}**",
            color=disnake.Color.purple(),
        )
        author_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else self.bot.user.display_avatar.url
        )
        respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
        await interaction.edit_original_message(embed=respEmbed)

    ## Other things ##

    ### Autocomplete for forum deletion ###

    @forum_rem.autocomplete("forum")
    async def removeforum_autocomplete(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
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
    bot.add_cog(ForumsModule(bot))
