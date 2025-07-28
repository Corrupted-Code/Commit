"""GPL-3.0 License"""

import datetime

import disnake

from disnake.ext import commands


class ListenerModule(commands.Cog):
    """Cog for handling various events in the bot"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        self.bot.ensure_defaults()
        await self.bot.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.watching, name="за форумами"
            )
        )
        print("------------")
        print(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        print("------------")

        data = self.bot.load_data()
        for _, d in data.items():
            if "threads" in d:
                for tid in list(d["threads"].keys()):
                    self.bot.loop.create_task(
                        self.bot.check_inactivity_thread(int(tid))
                    )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        """Called when the bot joins a new guild"""
        print("DEBUG: Bot has been added to a new guild:", guild.name)
        self.bot.ensure_defaults()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Called when a message is sent in a guild or DM"""
        if message.author.bot:
            return

        if isinstance(message.channel, disnake.Thread):
            data = self.bot.load_data()
            sid = str(message.guild.id)
            tid = str(message.channel.id)

            if sid in data and "threads" in data[sid] and tid in data[sid]["threads"]:
                author_id = data[sid]["threads"][tid]["author"]
                if message.author.id != author_id:
                    close_after = data[sid].get("closeAfter", 1)
                    data[sid]["threads"][tid]["end_time"] = (
                        disnake.utils.utcnow() + datetime.timedelta(hours=close_after)
                    ).isoformat()
                    self.bot.save_data(data)

        # await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: disnake.Thread):
        """Called when a thread is created in a forum channel"""
        data = self.bot.load_data()
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
            welcome_formatted = welcome.format(
                thread_author=thread.owner.mention,
                thread_id=thread.id,
                thread_name=thread.name,
            )
            embed = disnake.Embed(
                description=welcome_formatted, color=disnake.Color.purple()
            )
            embed.set_footer(
                text="Made with ❤️ by PrivateKey",
                icon_url=self.bot.user.display_avatar.url,
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
        self.bot.save_data(data)

        self.bot.loop.create_task(self.bot.check_inactivity_thread(thread.id))

def setup(bot):
    """Setup function to connect ListenerModule"""
    bot.add_cog(ListenerModule(bot))
