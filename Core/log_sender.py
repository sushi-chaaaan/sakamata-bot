import os
from datetime import timedelta, timezone

from discord import ApplicationContext

import discord
from discord import Object
from discord.ext import commands

from . import embed_builder as EB


utc = timezone.utc
jst = timezone(timedelta(hours=9), "Asia/Tokyo")

log_channel = int(os.environ["LOG_CHANNEL"])


class LogSender(Object):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_exe_log(self, ctx: commands.Context, msg: str, desc_url: str):
        embed = EB.create_base_log_embed(ctx, msg, desc_url)
        channel = self.bot.get_channel(log_channel)
        await channel.send(embed=embed)
        return

    async def send_timeout_log(
        self, ctx: commands.Context, msg: str, desc_url: str, until: str
    ):
        embed = EB.create_base_log_embed(ctx, msg, desc_url)
        channel = self.bot.get_channel(log_channel)
        embed.insert_field_at(2, name="解除日時", value=until)
        await channel.send(embed=embed)
        return

    async def send_context_log(self, ctx: commands.Context, msg: str, desc_url: str):
        embed = EB.create_base_context_log_embed(ctx, msg, desc_url)
        channel = self.bot.get_channel(log_channel)
        await channel.send(embed=embed)
        return

    async def send_context_timeout_log(
        self, ctx: ApplicationContext, msg: str, desc_url: str, until_str: str
    ):
        embed = EB.create_base_context_log_embed(ctx, msg, desc_url)
        channel = self.bot.get_channel(log_channel)
        embed.insert_field_at(2, name="解除日時", value=f"{until_str}")
        await channel.send(embed=embed)
        return


def setup(bot):
    return bot.add_cog(LogSender(bot))
