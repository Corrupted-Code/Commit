# This project is licensed under GPL v3.

import disnake
import json
import os, sys
import asyncio
import traceback
import datetime
import uuid

from disnake.ext import commands
from disnake.ui import View, Button

import config as cfg

client = commands.Bot(command_prefix=cfg.PREFIX, intents=disnake.Intents.all())
DATA_FILE = "forums.json"
client.remove_command("help")


@client.event
async def on_guild_join(guild: disnake.Guild):
    print("DEBUG: Bot has been added to a new guild:", guild.name)
    ensure_defaults()


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def ensure_defaults():
    data = load_data()
    updated = False
    for guild in client.guilds:
        sid = str(guild.id)
        if sid not in data:
            data[sid] = {
                "forumchannels": [],
                "closeAfter": 1,
                "welcomeMessage": "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
                "delete_closed": True,
                "welcome_enabled": True,
            }
            updated = True
        else:
            if "forumchannels" not in data[sid]:
                data[sid]["forumchannels"] = []
                updated = True
            if "closeAfter" not in data[sid]:
                data[sid]["closeAfter"] = 1
                updated = True
            if "welcomeMessage" not in data[sid]:
                data[sid][
                    "welcomeMessage"
                ] = "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}"
                updated = True
            if "delete_closed" not in data[sid]:
                data[sid]["delete_closed"] = True
                updated = True
    if updated:
        save_data(data)


@client.event
async def on_ready():
    ensure_defaults()
    await client.change_presence(
        activity=disnake.Activity(
            type=disnake.ActivityType.watching, name="за форумами"
        )
    )
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")

    data = load_data()
    for sid, d in data.items():
        if "threads" in d:
            for tid in list(d["threads"].keys()):
                client.loop.create_task(check_inactivity_thread(int(tid)))


@client.command()
async def reboot(ctx):
    errEmbed = disnake.Embed(title="Ошибка", color=disnake.Color.red())
    user_avatar = (
        ctx.author.display_avatar.url
        if ctx.author.display_avatar
        else client.user.display_avatar.url
    )
    errEmbed.set_footer(text=f"{ctx.author.name}", icon_url=user_avatar)

    if ctx.author.id not in cfg.OWNER_IDS:
        errEmbed.description = "У вас нет прав на перезагрузку бота."
        return await ctx.send(embed=errEmbed, delete_after=10)

    confirmEmbed = disnake.Embed(
        title="Вы уверены что хотите перезапустить бота?", color=disnake.Color.orange()
    )
    confirmEmbed.set_footer(text=f"{ctx.author.name}", icon_url=user_avatar)

    class ConfirmView(View):
        def __init__(self):
            super().__init__(timeout=30)

        @disnake.ui.button(label="Да", style=disnake.ButtonStyle.green)
        async def yes(self, button: Button, interaction: disnake.MessageInteraction):
            if interaction.author.id not in cfg.OWNER_IDS:
                errEmbed.description = "У вас нет прав на выполнение этого действия."
                return await interaction.response.send_message(
                    embed=errEmbed, ephemeral=True
                )

            errEmbed.title = "Перезагрузка..."
            await interaction.response.edit_message(embed=errEmbed, view=None)

            await client.change_presence(
                activity=disnake.Activity(
                    type=disnake.ActivityType.watching, name="перезапуск"
                )
            )
            await asyncio.sleep(5)
            os.execv(sys.executable, [sys.executable] + sys.argv)

        @disnake.ui.button(label="Нет", style=disnake.ButtonStyle.red)
        async def no(self, button: Button, interaction: disnake.MessageInteraction):
            if interaction.author.id not in cfg.OWNER_IDS:
                errEmbed.description = "У вас нет прав на выполнение этого действия."
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


@client.slash_command(
    name="forum",
    description="Управление форумами",
    default_member_permissions=disnake.Permissions(manage_channels=True),
)
async def forum(interaction: disnake.CommandInteraction):
    if isinstance(interaction.channel, disnake.DMChannel):
        errEmbed = disnake.Embed(
            title="Ошибка",
            description="Эта команда недоступна в личных сообщениях.",
            color=disnake.Color.red(),
        )
        user_avatar = (
            interaction.author.display_avatar.url
            if interaction.author.display_avatar
            else client.user.display_avatar.url
        )
        errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=user_avatar)
        return await interaction.response.send_message(embed=errEmbed, ephemeral=True)
    pass


@client.slash_command(name="about", description="Информация о боте")
async def about(interaction: disnake.CommandInteraction):
    embed = disnake.Embed(
        title="О боте",
        description="Бот для управления вопросами в форумах для KDS.",
        color=disnake.Color.purple(),
    )
    embed.add_field(name="Версия", value=cfg.VERSION, inline=True)
    embed.set_footer(
        text=f"Made with ❤️ by PrivateKey2", icon_url=client.user.display_avatar.url
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.slash_command(name="help", description="Информация о боте")
async def about(interaction: disnake.CommandInteraction):
    embed = disnake.Embed(
        title="Команды",
        description="``!close`` - для закрытия вопроса/ветки в форуме которым я управляю.\n\nДля админов выберите все слеш команды от меня.",
        color=disnake.Color.purple(),
    )
    embed.set_footer(
        text=f"Made with ❤️ by PrivateKey2", icon_url=client.user.display_avatar.url
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@forum.sub_command(name="add", description="Создать новый форум")
async def forum_add(
    interaction: disnake.CommandInteraction,
    name: str = commands.Param(description="Название форума"),
):
    await interaction.response.defer(ephemeral=True)
    forum = await interaction.guild.create_forum_channel(name)
    data = load_data()
    sid = str(interaction.guild.id)
    if sid not in data:
        data[sid] = {
            "forumchannels": [],
            "closeAfter": 1,
            "welcomeMessage": "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
        }
    data[sid]["forumchannels"].append(forum.id)
    save_data(data)
    respEmbed = disnake.Embed(
        title="Форум создан",
        description=f"Форум **{name}** (ID: `{forum.id}`) создан.",
        color=disnake.Color.purple(),
    )
    author_avatar = (
        interaction.author.display_avatar.url
        if interaction.author.display_avatar
        else client.user.display_avatar.url
    )
    respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
    await interaction.edit_original_message(embed=respEmbed)


@forum.sub_command(
    name="toggle_message", description="Включить или выключить приветственное сообщение"
)
async def forum_welcome_toggle(
    interaction: disnake.CommandInteraction,
    value: bool = commands.Param(description="True - включить, False - выключить"),
):
    await interaction.response.defer(ephemeral=True)
    data = load_data()
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

    save_data(data)
    state = "включено" if value else "выключено"

    respEmbed = disnake.Embed(
        title="Настройки обновлены",
        description=f"Приветственное сообщение теперь **{state}**.",
        color=disnake.Color.purple(),
    )
    author_avatar = (
        interaction.author.display_avatar.url
        if interaction.author.display_avatar
        else client.user.display_avatar.url
    )
    respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
    await interaction.edit_original_message(embed=respEmbed)


@forum.sub_command(name="close_after", description="Установить время закрытия до ветки")
async def set_config(
    interaction: disnake.CommandInteraction,
    hours: int = commands.Param(description="Время в часах."),
):
    await interaction.response.defer(ephemeral=True)
    data = load_data()
    sid = str(interaction.guild.id)
    if sid not in data:
        data[sid] = {
            "forumchannels": [],
            "closeAfter": hours,
            "welcomeMessage": "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
        }
    else:
        data[sid]["closeAfter"] = hours
    save_data(data)
    respEmbed = disnake.Embed(
        title="Настройки форума обновлены",
        description=f"Ветки автоматически закрываются после: {hours} часов инактива.",
        color=disnake.Color.purple(),
    )
    author_avatar = (
        interaction.author.display_avatar.url
        if interaction.author.display_avatar
        else client.user.display_avatar.url
    )
    respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
    await interaction.edit_original_message(embed=respEmbed)


@forum.sub_command(name="message", description="Установить приветственное сообщение")
async def forum_welcome_message(interaction: disnake.CommandInteraction):
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
            data = load_data()
            sid = str(modal_inter.guild.id)
            if sid not in data:
                data[sid] = {
                    "forumchannels": [],
                    "closeAfter": 1,
                    "welcomeMessage": msg,
                }
            else:
                data[sid]["welcomeMessage"] = msg
            save_data(data)
            respEmbed = disnake.Embed(
                title="Настройки обновлены",
                description=f"Приветственное сообщение:\n```{msg}```",
                color=disnake.Color.purple(),
            )
            author_avatar = (
                interaction.author.display_avatar.url
                if interaction.author.display_avatar
                else client.user.display_avatar.url
            )
            await modal_inter.response.send_message(embed=respEmbed, ephemeral=True)

    await interaction.response.send_modal(modal=WelcomeModal())


@forum.sub_command(
    name="deleteclosed", description="Включить/выключить кнопку удаления закрытых веток"
)
async def forum_delete_closed(
    interaction: disnake.CommandInteraction,
    value: bool = commands.Param(description="True или False"),
):
    await interaction.response.defer(ephemeral=True)
    data = load_data()
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
    save_data(data)
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
        else client.user.display_avatar.url
    )
    respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
    await interaction.edit_original_message(embed=respEmbed)


@forum.sub_command(name="rem", description="Удалить форум")
async def forum_rem(
    interaction: disnake.CommandInteraction,
    forum: str = commands.Param(description="Удаляемый форум", autocomplete=True),
):
    errEmbed = disnake.Embed(
        title="Упс!",
        color=disnake.Color.red(),
    )
    author_avatar = (
        interaction.author.display_avatar.url
        if interaction.author.display_avatar
        else client.user.display_avatar.url
    )
    errEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
    await interaction.response.defer(ephemeral=True)
    data = load_data()
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
    save_data(data)

    respEmbed = disnake.Embed(
        title="Форум удалён",
        description=f"Форум **{channel.name}** (ID: `{fid}`) был успешно удалён.",
        color=disnake.Color.purple(),
    )
    author_avatar = (
        interaction.author.display_avatar.url
        if interaction.author.display_avatar
        else client.user.display_avatar.url
    )
    respEmbed.set_footer(text=f"{interaction.author.name}", icon_url=author_avatar)
    await interaction.edit_original_message(embed=respEmbed)


@forum_rem.autocomplete("forum")
async def removeforum_autocomplete(
    inter: disnake.ApplicationCommandInteraction, user_input: str
):
    data = load_data()
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


async def send_close_embed(thread, closer, closer_type="автоматически"):
    data = load_data()
    sid = str(thread.guild.id)
    auto_delete = data.get(sid, {}).get("delete_closed", True)

    if closer_type == "автоматически":
        desc = "Ветка была закрыта автоматически (никто не ответил)."
        footer_text = client.user.name
        footer_icon = client.user.display_avatar.url
    elif closer_type == "автор":
        desc = "Ветка была закрыта автором."
        footer_text = closer.display_name
        footer_icon = closer.display_avatar.url
    else:
        desc = "Ветка была закрыта админом."
        footer_text = closer.display_name
        footer_icon = closer.display_avatar.url

    embed = disnake.Embed(
        title="Ветка закрыта",
        description=desc,
        color=disnake.Color.red(),
    )
    embed.set_footer(text=footer_text, icon_url=footer_icon)
    await thread.edit(archived=True)

    if auto_delete:
        await thread.send(embed=embed)
        await asyncio.sleep(15)
        await thread.delete()
    else:
        await thread.send(embed=embed)

    return True


@client.event
async def on_thread_create(thread: disnake.Thread):
    data = load_data()
    sid = str(thread.guild.id)
    if (
        sid not in data
        or "forumchannels" not in data[sid]
        or thread.parent_id not in data[sid]["forumchannels"]
    ):
        return

    if data[sid].get("welcome_enabled", True):
        welcome = data[sid].get(
            "welcomeMessage",
            "Hello! {thread_author}, welcome to your thread {thread_id} - {thread_name}",
        )
        welcomeFormatted = welcome.format(
            thread_author=thread.owner.mention,
            thread_id=thread.id,
            thread_name=thread.name,
        )
        embed = disnake.Embed(
            description=welcomeFormatted, color=disnake.Color.purple()
        )
        embed.set_footer(
            text=f"Made with ❤️ by PrivateKey2", icon_url=client.user.display_avatar.url
        )
        await thread.send(embed=embed)

    close_after = data[sid].get("closeAfter", 1)
    end_time = (
        disnake.utils.utcnow() + datetime.timedelta(hours=close_after)
    ).isoformat()

    if "threads" not in data[sid]:
        data[sid]["threads"] = {}
    data[sid]["threads"][str(thread.id)] = {
        "author": thread.owner_id,
        "end_time": end_time,
    }
    save_data(data)

    client.loop.create_task(check_inactivity_thread(thread.id))


async def check_inactivity_thread(thread_id: int):
    await asyncio.sleep(5)

    while True:
        await asyncio.sleep(300)
        data = load_data()

        sid = None
        for g, d in data.items():
            if "threads" in d and str(thread_id) in d["threads"]:
                sid = g
                break

        if not sid:
            return

        try:
            t = await client.fetch_channel(thread_id)
        except disnake.NotFound:
            del data[sid]["threads"][str(thread_id)]
            save_data(data)
            return

        if t.archived or t.locked:
            del data[sid]["threads"][str(thread_id)]
            save_data(data)
            return

        now = disnake.utils.utcnow()
        end_time = disnake.utils.parse_time(
            data[sid]["threads"][str(thread_id)]["end_time"]
        )

        if now >= end_time:
            try:
                await t.edit(locked=True, archived=True)
                await send_close_embed(t, client.user, "автоматически")
            except Exception:
                pass
            del data[sid]["threads"][str(thread_id)]
            save_data(data)
            return


@client.event
async def on_message(message: disnake.Message):
    if message.author.bot:
        return

    await client.process_commands()

    if not isinstance(message.channel, disnake.Thread):
        return

    data = load_data()
    sid = str(message.guild.id)
    tid = str(message.channel.id)

    if sid in data and "threads" in data[sid] and tid in data[sid]["threads"]:
        author_id = data[sid]["threads"][tid]["author"]
        if message.author.id != author_id:
            close_after = data[sid].get("closeAfter", 1)
            data[sid]["threads"][tid]["end_time"] = (
                disnake.utils.utcnow() + datetime.timedelta(hours=close_after)
            ).isoformat()
            save_data(data)

    await client.process_commands(message)


@client.command(name="close")
async def close_thread(ctx: commands.Context):
    errEmbed = disnake.Embed(
        title="Упс!",
        color=disnake.Color.red(),
    )
    author_avatar = (
        ctx.author.display_avatar.url
        if ctx.author.display_avatar
        else client.user.display_avatar.url
    )
    errEmbed.set_footer(text=f"{ctx.author.name}", icon_url=author_avatar)

    if not isinstance(ctx.channel, disnake.Thread):
        errEmbed.description = "Эта команда работает только в ветках."
        return await ctx.send(embed=errEmbed, delete_after=40)

    data = load_data()
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
        await send_close_embed(thread, ctx.author, "модератор")
    elif ctx.author.id == thread.owner_id:
        if thread.archived or thread.locked:
            return False
        await thread.edit(archived=True, locked=True)
        await send_close_embed(thread, ctx.author, "автор")
    else:
        errEmbed.description = "У вас нет прав закрывать эту ветку."
        await ctx.send(embed=errEmbed, delete_after=40)


@client.event
async def on_slash_command_error(
    inter: disnake.ApplicationCommandInteraction, error: Exception
):
    errEmbed = disnake.Embed(title="Ошибка", color=disnake.Color.red())
    user_avatar = (
        inter.author.display_avatar.url
        if inter.author.display_avatar
        else client.user.display_avatar.url
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


client.run(cfg.TOKEN)
