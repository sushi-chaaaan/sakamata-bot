import asyncio
from datetime import datetime, timedelta, timezone
import os

import discord
from discord.commands import slash_command
from discord.ext import commands
from discord.ext.ui import (Button, InteractionProvider, MessageProvider, Message, View,
                            ViewTracker, state)
from Cogs.connect import connect

guild_id = int(os.environ['GUILD_ID'])
process_channel = int(os.environ['PROCESS_CATEGORY'])
utc = timezone.utc
jst = timezone(timedelta(hours=9), 'Asia/Tokyo')
conn = connect()


class Process(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(guild_ids=[guild_id], name='process')
    async def _start_game(self, ctx: discord.ApplicationContext) -> None:
        session_id: int = ctx.interaction.id
        view = CloseButton(ctx, session_id)
        tracker = ViewTracker(view, timeout=None)
        await tracker.track(InteractionProvider(ctx.interaction, ephemeral=True))
        conn.set(f'{session_id}.status', 'open', ex=1200)
        await self._send_invite(ctx, session_id)
        return

    async def _send_invite(self, ctx: discord.ApplicationContext, session_id: int):
        print('launched')
        channel = ctx.interaction.channel
        start_time = discord.utils.utcnow()
        exp_time = start_time + timedelta(minutes=10.0)
        view = JoinButton(ctx, start_time, exp_time)
        tracker = ViewTracker(view, timeout=30)
        await tracker.track(MessageProvider(channel))
        for i in range(30):
            if conn.get(f'{session_id}.status') == 'open':
                await asyncio.sleep(1)
            else:
                break
        """
        message_id: [user_id, user_id...]
        """
        ids = conn.smembers(str(tracker.message.id))
        print(ids)
        conn.delete(str(tracker.message.id))
        target = tracker.message.embeds[0]
        target.title = 'この募集は終了しました。'
        await tracker.message.edit(embeds=[target], view=None)
        return


class CloseButton(View):
    status = state('status')
    l_str = state('l_str')
    r_str = state('r_str')
    text = state('text')
    title = state('title')

    def __init__(self, ctx, session_id: int):
        super().__init__()
        self.ctx = ctx
        self.l_str = '締め切り'
        self.r_str = '取り消し'
        self.status = None
        self.title = '募集を開始しました。'
        self.text = '締め切る際は締め切りボタンを押してください。\n募集を取り消す場合は取り消しボタンを押してください。'
        self.session_id = session_id

    async def _ok(self, interaction: discord.Interaction):
        self.status = True
        self.title = '募集を締め切りました。'
        self.text = 'このメッセージを消去してスレッドでゲームを開始してください。'
        conn.set(f'{self.session_id}.status', 'close', ex=1200)
        self.stop()

    async def _ng(self, interaction: discord.Interaction):
        self.status = False
        self.title = '募集を取り消しました。'
        self.text = 'このメッセージを消去してください。'
        self.stop()

    async def body(self) -> Message:
        return Message(
            embeds=[
                discord.Embed(
                    title=self.title,
                    description=self.text,
                    color=15767485,
                ),
            ],
            components=[
                Button(self.l_str).style(discord.ButtonStyle.blurple).disabled(
                    self.status is not None).on_click(self._ok),
                Button(self.r_str).style(discord.ButtonStyle.red).disabled(
                    self.status is not None).on_click(self._ng)
            ]
        )


class JoinButton(View):
    status = state('status')
    title = state('title')
    label = state('label')

    def __init__(self, ctx, start: datetime, exp: datetime):
        super().__init__()
        self.ctx = ctx
        self.label = '参加'
        self.status = None
        self.start = start
        self.exp = exp

    async def _ok(self, interaction: discord.Interaction):
        if not str(interaction.user.id) in conn.smembers(str(interaction.message.id)):
            conn.sadd(str(interaction.message.id), str(interaction.user.id))
            if not interaction.response.is_done():
                await interaction.response.send_message('参加登録を行いました！\n開始までしばらくお待ちください！', ephemeral=True)
            else:
                await interaction.followup.send(content='参加登録を行いました！\n開始までしばらくお待ちください！', ephemeral=True)
            return
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message('既に参加登録したユーザーです。', ephemeral=True)
            else:
                await interaction.followup.send(content='既に参加登録したユーザーです。', ephemeral=True)

    async def body(self) -> Message:
        exp_str = self.exp.astimezone(jst).strftime('%Y/%m/%d %H:%M:%S')
        embed = discord.Embed(
            title='募集が開始されました。',
            description=f'有効期限:{exp_str}',
            color=15767485,
        )
        embed.set_author(
            name=self.ctx.interaction.user,
            icon_url=self.ctx.interaction.user.avatar.url
        )
        return Message(
            embeds=[embed],
            components=[
                Button(self.label).style(discord.ButtonStyle.blurple).disabled(
                    self.status is not None).on_click(self._ok),
            ]
        )


"""
定義:

1.チャンネルで開始コマンドを実行。
2.募集を開始(未定)
3.参加者のみのスレッドを親チャンネルから作成してゲームを進行
4.募集ちゃんねるに募集中のゲームと進行中のゲームが出せたらいいね
"""


def setup(bot):
    return bot.add_cog(Process(bot))
