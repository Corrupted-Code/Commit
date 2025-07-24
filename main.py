# This project is licensed under GPL-v3.

import disnake
import json
import os
import asyncio
import time

from disnake.ext import commands

import config as cfg

client = commands.Bot(command_prefix=cfg.PREFIX, intents=disnake.Intents.all())
DATA_FILE = "forums.json"
client.remove_command("help")

start_time = time.time()


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


# Setup functions and vars
client.load_data = load_data
client.save_data = save_data
client.ensure_defaults = ensure_defaults
client.check_inactivity_thread = check_inactivity_thread
client.send_close_embed = send_close_embed
client.start_time = start_time

# Load cogs
for filename in os.listdir("./modules"):
    if filename.endswith(".py"):
        cog_name = f"modules.{filename[:-3]}"
        try:
            client.load_extension(cog_name)
            print(f"Debug: Ког {filename} загружен")
        except Exception as e:
            print(f"ERR: Ког {filename} не удалось загрузить: {e}")

client.run(cfg.TOKEN)
