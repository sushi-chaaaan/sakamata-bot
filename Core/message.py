import os

import discord
import requests
from discord.ext import commands
from newdispanderfixed import dispand

from Core.confirm import Confirm
from Core.log_sender import LogSender as LS

admin_role = int(os.environ["ADMIN_ROLE"])


class Message_Sys(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message_dispand(self, message: discord.Message):
        avoid_word_list_prefix = ["//send-message", "//edit-message", "//send-dm"]
        if type(message.channel) == discord.DMChannel:
            return
        else:
            for word in avoid_word_list_prefix:
                if message.content.startswith(word):
                    return
            if message.content.endswith("中止に必要な承認人数: 1"):
                return
            else:
                await dispand(self.bot, message)
                return

    @commands.command(name="send-message")
    @commands.has_role(admin_role)
    async def _send(self, ctx: commands.Context, channel_id: str, *, text: str):
        """メッセージ送信用"""
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            channel = await self.bot.fetch_channel(int(channel_id))
        permitted_role = ctx.guild.get_role(admin_role)
        confirm_msg = f"【メッセージ送信確認】\n以下のメッセージを{channel.mention}へ送信します。"
        exe_msg = f"{channel.mention}にメッセージを送信しました。"
        non_exe_msg = f"{channel.mention}へのメッセージ送信をキャンセルしました。"
        confirm_arg = f"\n{text}\n------------------------"
        if ctx.message.attachments:
            files: list[discord.File] = [
                await attachment.to_file() for attachment in ctx.message.attachments
            ]
            result = await Confirm(self.bot).confirm(
                ctx, confirm_arg, permitted_role, confirm_msg, files
            )
        else:
            files = []
            result = await Confirm(self.bot).confirm(
                ctx, confirm_arg, permitted_role, confirm_msg
            )
        if result:
            if files != []:
                sent_message = await channel.send(content=text, files=files)
            else:
                sent_message = await channel.send(content=text)
            msg = exe_msg
            desc_url = sent_message.jump_url
            await ctx.send("Sended!")
        else:
            msg = non_exe_msg
            desc_url = ""
            await ctx.send("Cancelled!")
        await LS(self.bot).send_exe_log(ctx, msg, desc_url)
        return

    @commands.command(name="edit-message")
    @commands.has_role(admin_role)
    async def _editmessage(
        self, ctx: commands.Context, channel_id: int, message_id: int, *, text: str
    ):
        """メッセージ編集用"""
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            channel = await self.bot.fetch_channel(int(channel_id))
        permitted_role = ctx.guild.get_role(admin_role)
        target = await channel.fetch_message(message_id)
        msg_url = (
            f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"
        )
        confirm_msg = f"【メッセージ編集確認】\n{channel.mention}のメッセージ\n{msg_url}\nを以下のように編集します。"
        exe_msg = f"{channel.mention}のメッセージを編集しました。"
        non_exe_msg = f"{channel.mention}のメッセージの編集をキャンセルしました。"
        confirm_arg = f"\n{text}\n------------------------"
        if ctx.message.attachments:
            files: list[discord.File] = [
                await attachment.to_file() for attachment in ctx.message.attachments
            ]

            result = await Confirm(self.bot).confirm(
                ctx, confirm_arg, permitted_role, confirm_msg, files
            )
        else:
            files = []
            result = await Confirm(self.bot).confirm(
                ctx, confirm_arg, permitted_role, confirm_msg
            )
        if result:
            if files != []:
                names = []
                for attachment in ctx.message.attachments:
                    names.append(attachment.filename)
                    if attachment.proxy_url:
                        download(attachment.filename, attachment.proxy_url)
                    else:
                        download(attachment.filename, attachment.url)
                # print("complete download")
                sent_files = [
                    discord.File(
                        os.path.join(os.path.dirname(__file__), f"/tmp/{name}"),
                        filename=name,
                        spoiler=False,
                    )
                    for name in names
                ]
                sent_message = await target.edit(content=text, files=sent_files)
                for name in names:
                    os.remove(os.path.join(os.path.dirname(__file__), f"/tmp/{name}"))
                # print("complete delete")
            else:
                sent_message = await target.edit(content=text)
            msg = exe_msg
            desc_url = sent_message.jump_url
            await ctx.send("Edited!")
        else:
            msg = non_exe_msg
            desc_url = ""
            await ctx.send("Cancelled!")
        await LS(self.bot).send_exe_log(ctx, msg, desc_url)
        return


def download(title, url):
    try:
        r = requests.get(url, stream=True)
        # openの中で保存先のパス（ファイル名を指定）
        with open("/tmp/" + title, mode="wb") as f:
            f.write(r.content)
    except requests.exceptions.RequestException as err:
        print(err)


def setup(bot):
    return bot.add_cog(Message_Sys(bot))
