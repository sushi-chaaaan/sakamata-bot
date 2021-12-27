import asyncio
import os
import sys
import traceback
from datetime import datetime, timedelta
from logging import debug

import discord
import requests
from discord import channel
from discord.channel import DMChannel
from discord.ext import commands
from discord.ext.commands.core import dm_only, has_role
from dispanderfixed import dispand

'''bot招待リンク
https://discord.com/api/oauth2/authorize?client_id=916956842440151070&permissions=543816019030&scope=bot
'''

### イベントハンドラ一覧(client) #################################################
# async def の後を変えるだけで実行されるイベンドが変わる
# メッセージ受信時に実行：   on_message(message)
# Bot起動時に実行：      on_ready(message)
# リアクション追加時に実行:  on_reaction_add(reaction, user)
# 新規メンバー参加時に実行： on_member_join(member)
# ボイスチャンネル出入に実行： on_voice_state_update(member, before, after)
###################################################################

#onlinetoken@heroku
token = os.environ['DISCORD_BOT_TOKEN']

#help-command-localize-test
class JapaneseHelpCommand(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__()
        self.commands_heading = "コマンド:"
        self.no_category = "利用可能なコマンド"
        self.command_attrs["help"] = "コマンド一覧と簡単な説明を表示"

    def get_ending_note(self):
        return (f"各コマンドの説明: /help <コマンド名>\n"
                f"各カテゴリの説明: /help <カテゴリ名>\n")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/',intents=intents,help_command=JapaneseHelpCommand())


'''
#本番鯖IDなど

guildid = 915910043461890078
logchannel = 917009541433016370
vclogchannel = 917009562383556678
commandchannel = 917788634655109200
dmboxchannel = 921781301101613076
siikuinrole = 915915792275632139
errorlogchannel = 924142068484440084
alertchannel = 924744385902575616
modrole = 916726433445986334
adminrole = 915954009343422494

'''
#実験鯖IDなど
guildid = 916965252896260117
logchannel = 916971090042060830
vclogchannel = 916988601902989373
commandchannel = 917788514903539794
dmboxchannel = 918101377958436954
siikuinrole = 923719282360188990
errorlogchannel = 924141910321426452
alertchannel = 924744469327257602
modrole = 924355349308383252
adminrole = 917332284582031390

#emoji
maruemoji = "\N{Heavy Large Circle}"
batuemoji = "\N{Cross Mark}"

#Bootmsg-serverlogchannel/console
async def greet():
    channel = bot.get_channel(logchannel)
    now = datetime.utcnow() + timedelta(hours=9)
    await channel.send(f'起動完了({now:%m/%d-%H:%M:%S})')

@bot.event
async def on_ready():
    print('logged in as {0.user}'.format(bot))
    await greet()

#error-log
@bot.event
async def on_command_error(ctx,error):
    channel = bot.get_channel(errorlogchannel)
    now = datetime.utcnow() + timedelta(hours=9)
    await channel.send(f'```エラーが発生しました。({now:%m/%d %H:%M:%S})\n{str(error)}```')

#error-logtest
@bot.command()
@commands.has_role(adminrole)
async def errortest(ctx):
    prin()

#Detect-NGword
@bot.listen('on_message')
async def detect_NGword(message):
    word_list = ['@everyone','@here']
    if any(x in message.content for x in word_list) == True:
        channel = bot.get_channel(alertchannel)
        embed = discord.Embed(
        title='NGワードを検知しました。',
        url=message.jump_url,
        color=16711680,
        description=message.content,
        timestamp=message.created_at
        )
        embed.set_author(
        name=message.author.display_name,
        icon_url=message.author.avatar_url
        )
        embed.add_field(
            name='送信者',
            value=f'{message.author.mention}'
        )
        embed.add_field(
            name='送信先',
            value=f'{message.channel.mention}'
        )
        embed.add_field(
            name='送信日時',
            value=f'{message.created_at + timedelta(hours=9):%Y/%m/%d %H:%M:%S}'
        )
        await channel.send(embed=embed)
    else:
        return

#Dispander-All
@bot.listen('on_message')
async def on_message_dispand(message):
    if type(message.channel) == discord.DMChannel:
        return
    elif message.content.startswith(('/send-message','/edit-message','/send-dm')):
        return
    elif message.content.endswith('中止に必要な承認人数: 1'):
        return
    else:
        await dispand(message)

'''
デフォルトで提供されている on_message をオーバーライドすると、コマンドが実行されなくなります。
これを修正するには on_message の最後に bot.process_commands(message) を追加してみてください。
https://discordbot.jp/blog/17/
'''

#VC入退室ログ
@bot.listen()
async def on_voice_state_update(member,before,after) :
    if member.guild.id == guildid and (before.channel != after.channel):
        channel = bot.get_channel(vclogchannel)
        now = datetime.utcnow() + timedelta(hours=9)
        vclogmention = member.mention
        if before.channel is None:
            msg = f'{now:%m/%d %H:%M:%S} : {vclogmention} が {after.channel.mention} に参加しました。'
            await channel.send(msg)
        elif after.channel is None:
            msg = f'{now:%m/%d %H:%M:%S} : {vclogmention} が {before.channel.mention} から退出しました。'
            await channel.send(msg)
        else:
            msg = f'{now:%m/%d %H:%M:%S} : {vclogmention} が {before.channel.mention} から {after.channel.mention} に移動しました。'
            await channel.send(msg)

#hello?
@bot.command()
@commands.has_role(modrole)
async def test(ctx):
    """生存確認用"""
    await ctx.send('hello')

#user-info-command
@bot.command()
@commands.has_role(modrole)
async def user(ctx,id:int):
    """ユーザー情報取得"""
#    guild = bot.get_guild(guildid)
#    member = guild.get_member(id)
    member = ctx.guild.get_member(id)
    #この先表示する用
    memberifbot = member.bot
    memberregdate = member.created_at + timedelta(hours=9)
    #NickNameあるか？
    if member.display_name == member.name :
        memberifnickname = 'None'
    else:
        memberifnickname = member.display_name
    memberid = member.id
    memberjoindate = member.joined_at + timedelta(hours=9)
    membermention = member.mention
    memberroles = member.roles
    #Message成形-途中
    userinfomsg = f'```ユーザー名:{member} (ID:{memberid})\nBot?:{memberifbot}\nニックネーム:{memberifnickname}\nアカウント作成日時:{memberregdate:%Y/%m/%d %H:%M:%S}\n参加日時:{memberjoindate:%Y/%m/%d %H:%M:%S}\n所持ロール:{memberroles}```'
    await ctx.send(userinfomsg)

#ping-test
@bot.command()
@commands.has_role(adminrole)
async def ping(ctx):
    """生存確認用"""
    rawping = bot.latency
    ping = round(rawping * 1000)
    await ctx.send(f'Ping is {ping}ms')

#recieve-dm
@bot.listen('on_message')
async def on_message_dm(message):
    if message.author.bot:
        return
    elif type(message.channel) == discord.DMChannel and bot.user == message.channel.me:
        channel = bot.get_channel(dmboxchannel)
        embed = discord.Embed(
        title='DMを受信しました。',
        url=message.jump_url,
        color=3447003,
        description=message.content,
        timestamp=message.created_at
        )
        embed.set_author(
        name=message.author.display_name,
        icon_url=message.author.avatar_url
        )
        embed.add_field(
            name='送信者',
            value=f'{message.author.mention}'
        )
        embed.add_field(
            name='受信日時',
            value=f'{message.created_at + timedelta(hours=9):%Y/%m/%d %H:%M:%S}'
        )
        await channel.send(embed=embed)
    else:
        return

#send-message
@bot.command(name='send-message')
@commands.has_role(adminrole)
async def _messagesend(ctx,channelid:int,*,arg):
    """メッセージ送信用"""
    #channel:送信先
    channel=bot.get_channel(channelid)
    #role:承認可能ロール
    role = ctx.guild.get_role(adminrole)
    kakuninmsg = f'【メッセージ送信確認】\n以下のメッセージを{channel.mention}へ送信します。'
    exemsg = f'{channel.mention}にメッセージを送信しました。'
    nonexemsg = f'{channel.mention}へのメッセージ送信をキャンセルしました。'
    arg = f'\n{arg}\n------------------------'
    turned = await confirm(ctx,arg,role,kakuninmsg)
    if turned == 'ok':
        msg=exemsg
        m = await channel.send(arg)
        descurl = m.jump_url
        await ctx.send('Sended!')
        await sendexelog(ctx,msg,descurl)
    elif turned == 'cancel':
        msg=nonexemsg
        descurl = ''
        await sendexelog(ctx,msg,descurl)
        await ctx.send('Cancelled!')
    else:
        return

#send-dm
@bot.command(name='send-dm')
@commands.has_role(adminrole)
async def _dmsend(ctx,id:int,*,arg):
    """DM送信用"""
    user = bot.get_user(id)
    role = ctx.guild.get_role(adminrole)
    kakuninmsg = f'【DM送信確認】\n以下のDMを{user.mention}へ送信します。'
    exemsg = f'{user.mention}にDMを送信しました。'
    nonexemsg = f'{user.mention}へのDM送信をキャンセルしました。'
    arg = f'\n{arg}\n------------------------'
    turned = await confirm(ctx,arg,role,kakuninmsg)
    if turned == 'ok':
        msg=exemsg
        m = await user.send(arg)
        descurl = m.jump_url
        await ctx.send('Sended!')
        await sendexelog(ctx,msg,descurl)
    elif turned == 'cancel':
        msg=nonexemsg
        descurl = ''
        await sendexelog(ctx,msg,descurl)
        await ctx.send('Cancelled!')
    else:
        return

#edit-message
@bot.command(name='edit-message')
@commands.has_role(adminrole)
async def _editmessage(ctx,channelid:int,messageid:int,*,arg):
    """メッセージ編集用"""
    channel=bot.get_channel(channelid)
    role = ctx.guild.get_role(adminrole)
    msgid = await channel.fetch_message(messageid)
    msgurl = f'https://discord.com/channels/{guildid}/{channelid}/{messageid}'
    kakuninmsg = f'【メッセージ編集確認】\n{channel.mention}のメッセージ\n{msgurl}\nを以下のように編集します。'
    exemsg = f'{channel.mention}のメッセージを編集しました。'
    nonexemsg = f'{channel.mention}のメッセージの編集をキャンセルしました。'
    arg = f'\n{arg}\n------------------------'
    turned = await confirm(ctx,arg,role,kakuninmsg)
    if turned == 'ok':
        msg=exemsg
        await msgid.edit(content=arg)
        descurl = msgurl
        await ctx.send('Edited!')
        await sendexelog(ctx,msg,descurl)
    elif turned == 'cancel':
        msg=nonexemsg
        descurl = ''
        await sendexelog(ctx,msg,descurl)
        await ctx.send('Cancelled!')
    else:
        return

#deal-member
#deal:対処。ban/kick
deal = None
#adddm:デフォルトDMに追加で送信するコンテンツ
adddm = None

#kick-member
@bot.command(name='kick')
@commands.has_role(adminrole)
async def _kickuser(ctx,id:int,ifdm:str='True'):
    member = ctx.guild.get_member(id)
    role = ctx.guild.get_role(adminrole)
    validifdm = ['True','False']
    if ifdm not in validifdm:
        await ctx.reply(content='不明な引数を検知したため処理を終了しました。\nDM送信をOFFにするにはFalseを指定してください。',mention_author=False)
        msg = '不明な引数を検知したため処理を終了しました。'
        descurl = ''
        await sendexelog(ctx,msg,descurl)
        return
    else:
        deal = 'kick'
        adddm = ''
        DMcontent = await makedealdm(ctx,deal,adddm)
        if ifdm == 'False':
            DMcontent = ''
        else:
            pass
        kakuninmsg = f'【kick実行確認】\n実行者:{ctx.author.display_name}(アカウント名:{ctx.author},ID:{ctx.author.id})\n対象者:\n　{member}(ID:{member.id})\nDM送信:{ifdm}\nDM内容:{DMcontent}'
        exemsg = f'{member.mention}をキックしました。'
        nonexemsg = f'{member.mention}のキックをキャンセルしました。'
        arg = ''
        turned = await confirm(ctx,arg,role,kakuninmsg)
        if turned == 'ok':
            msg = exemsg
            if ifdm == 'True':
                m = await member.send(DMcontent)
                descurl = m.jump_url
                await member.kick(reason = None)
                await ctx.send('kicked!')
                await sendexelog(ctx,msg,descurl)
                return
            elif ifdm == 'False':
                descurl = ''
                await member.kick(reason = None)
                await ctx.send('kicked!')
                await sendexelog(ctx,msg,descurl)
                return
            else:
                return
        elif turned == 'cancel':
            msg=nonexemsg
            descurl = ''
            await sendexelog(ctx,msg,descurl)
            await ctx.send('Cancelled!')
        else:
            return

#ban-member
@bot.command(name='ban')
@commands.has_role(adminrole)
async def _banuser(ctx,id:int,ifdm:str='True'):
    member = ctx.guild.get_member(id)
    role = ctx.guild.get_role(adminrole)
    validifdm = ['True','False']
    if ifdm not in validifdm:
        await ctx.reply(content='不明な引数を検知したため処理を終了しました。\nDM送信をOFFにするにはFalseを指定してください。',mention_author=False)
        msg = '不明な引数を検知したため処理を終了しました。'
        descurl = ''
        await sendexelog(ctx,msg,descurl)
        return
    else:
        deal = 'ban'
        adddm = '''
今後、あなたはクロヱ水族館に参加することはできません。

BANの解除を希望する場合は以下のフォームをご利用ください。
クロヱ水族館BAN解除申請フォーム
https://forms.gle/mR1foEyd9JHbhYdCA
'''
        DMcontent = await makedealdm(ctx,deal,adddm)
        if ifdm == 'False':
            DMcontent = ''
        else:
            pass
        kakuninmsg = f'【ban実行確認】\n実行者:{ctx.author.display_name}(アカウント名:{ctx.author},ID:{ctx.author.id})\n対象者:\n　{member}(ID:{member.id})\nDM送信:{ifdm}\nDM内容:{DMcontent}'
        exemsg = f'{member.mention}をBANしました。'
        nonexemsg = f'{member.mention}のBANをキャンセルしました。'
        arg = ''
        turned = await confirm(ctx,arg,role,kakuninmsg)
        if turned == 'ok':
            msg = exemsg
            if ifdm == 'True':
                m = await member.send(DMcontent)
                descurl = m.jump_url
                await member.ban(reason = None)
                await ctx.send('baned!')
                await sendexelog(ctx,msg,descurl)
                return
            elif ifdm == 'False':
                descurl = ''
                await member.ban(reason = None)
                await ctx.send('baned!')
                await sendexelog(ctx,msg,descurl)
                return
            else:
                return
        elif turned == 'cancel':
            msg=nonexemsg
            descurl = ''
            await ctx.send('Cancelled!')
            await sendexelog(ctx,msg,descurl)
        else:
            return

#Unban
@bot.command(name='unban')
@commands.has_role(adminrole)
async def _unbanuser(ctx,id:int):
    user = bot.fetch_user(id)
    role = ctx.guild.get_role(adminrole)
    kakuninmsg = f'【Unban実行確認】\n実行者:{ctx.author.display_name}(アカウント名:{ctx.author},ID:{ctx.author.id})\n対象者:\n　{user}(ID:{user.id})'
    exemsg = f'{user.mention}をBANを解除しました。'
    nonexemsg = f'{member.mention}のBANの解除をキャンセルしました。'
    arg = ''
    turned = await confirm(ctx,arg,role,kakuninmsg)
    if turned == 'ok':
        msg = exemsg
        descurl = ''
        await ctx.guild.unban(user)
        await ctx.send('Unbaned!')
        await sendexelog(ctx,msg,descurl)
    elif turned == 'cancel':
        msg=nonexemsg
        descurl = ''
        await ctx.send('Cancelled!')
        await sendexelog(ctx,msg,descurl)
    else:
        return

#Deal-DM
async def makedealdm(ctx,deal,adddm):
    DMcontent = f'''【あなたは{str.upper(deal)}されました】
クロヱ水族館/Chloeriumの管理者です。

あなたのサーバーでの行為がサーバールールに違反していると判断し、{str.upper(deal)}しました。
{adddm}'''
    return DMcontent

#confirm-system
async def confirm(ctx,arg,role,kakuninmsg):
    sendkakuninmsg = f'{kakuninmsg}\n------------------------{arg}\nコマンド承認:{role.mention}\n実行に必要な承認人数: 1\n中止に必要な承認人数: 1'
    m = await ctx.send(sendkakuninmsg)
    await m.add_reaction(maruemoji)
    await m.add_reaction(batuemoji)
    valid_reactions = [maruemoji,batuemoji]
    #wait-for-reaction
    def check(reaction,user):
        return role in user.roles and str(reaction.emoji) in valid_reactions
    reaction,user = await bot.wait_for('reaction_add',check = check)
    #exe
    if str(reaction.emoji) == maruemoji:
        return 'ok'
    else:
        return 'cancel'

#send-exe-log
async def sendexelog(ctx,msg,descurl):
    channel = bot.get_channel(logchannel)
    embed = discord.Embed(
    title = '実行ログ',
    color = 3447003,
    description = msg,
    url = f'{descurl}',
    timestamp=datetime.utcnow()
    )
    embed.set_author(
    name=bot.user,
    icon_url=bot.user.avatar_url
    )
    embed.add_field(
        name='実行者',
        value=f'{ctx.author.mention}'
    )
    embed.add_field(
        name='実行コマンド',
        value=f'[コマンドリンク]({ctx.message.jump_url})'
    )
    embed.add_field(
        name='実行日時',
        value=f'{datetime.utcnow() + timedelta(hours=9):%Y/%m/%d %H:%M:%S}'
    )
    await channel.send(embed=embed)

bot.run(token)
