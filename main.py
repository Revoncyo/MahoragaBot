import discord
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timedelta, timezone
import yt_dlp as youtube_dl
import requests
import xml.etree.ElementTree as ET
import os
from flask import Flask
from threading import Thread

# --- GÜVENLİK VE AYARLAR ---
# ARTIK TOKEN BURAYA YAZILMIYOR!
# Render'ın ayarlarından otomatik çekecek.
TOKEN = os.environ.get('TOKEN') 
PREFIX = '!'

# --- WANS STUDIOS BİLGİLERİ ---
WEBSITE_URL = "https://wansstudioskeyal.wuaze.com/?pass=WansSecretPass2026"
SCRIPT_CODE = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/Revoncyo/Driving-Empire-Car-Racing-Atm-Script/refs/heads/main/DrivingEmpire.lua"))()'
ROBLOX_GROUP = "https://www.roblox.com/tr/communities/35620134/Wans-Studios#!/about"
NOTIFICATION_CHANNEL_ID = 1466233645063868642 
# YouTube ID'sini de buraya direkt yazabilirsin
YOUTUBE_CHANNEL_ID = "UCVBScxCGhrwk4UUVCOrd1UQ"

BAD_WORDS = ["fuck", "bitch", "shit", "asshole", "dick", "bastard", "cunt", "whore", "slut", "faggot", "nigger", "nigga", "idiot", "stupid", "stfu", "kys"]
MIN_ACCOUNT_AGE_DAYS = 7

# --- WEB SERVER (Render İçin) ---
app = Flask('')
@app.route('/')
def home():
    return "Mahoraga is awake!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT KURULUMU ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# --- MÜZİK AYARLARI ---
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}
ffmpeg_options = {'options': '-vn', "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        if not url.startswith("http"):
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{url}", download=not stream))
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data: data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f'{bot.user} (Mahoraga) has been summoned!')
    change_status.start()
    check_youtube.start()

@tasks.loop(seconds=20)
async def change_status():
    statuses = ["Adapting to Scripts... ⚙️", "Wheel is turning... ☸️", f"{PREFIX}key for Power 🔑", "Guarding Wans Studios 🛡️"]
    await bot.change_presence(activity=discord.Game(name=random.choice(statuses)))

@bot.event
async def on_member_join(member):
    # Anti-Alt Hesap
    account_age = datetime.now(timezone.utc) - member.created_at
    if account_age.days < MIN_ACCOUNT_AGE_DAYS:
        try:
            await member.send(f"⚠️ **Access Denied.** Your account is too new ({account_age.days} days).")
            await member.kick(reason="Anti-Alt Protection")
            return
        except: pass
    
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        embed = discord.Embed(title="Mahoraga Summoned You!", description=f"Welcome {member.mention} to **Wans Studios**.", color=0x8B0000)
        embed.set_thumbnail(url="https://i.pinimg.com/originals/82/32/7a/82327a42168538d62650742512a4505f.jpg")
        embed.add_field(name="🔑 Get Key", value=f"[Access Power]({WEBSITE_URL})", inline=True)
        embed.add_field(name="👥 Group", value=f"[Join Army]({ROBLOX_GROUP})", inline=True)
        await channel.send(embed=embed)

@tasks.loop(minutes=10)
async def check_youtube():
    if "UC" not in YOUTUBE_CHANNEL_ID: return
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        response = requests.get(url)
        if response.status_code == 200:
            tree = ET.fromstring(response.content)
            ns = '{http://www.w3.org/2005/Atom}'
            entry = tree.find(f'{ns}entry')
            if entry:
                video_id = entry.find(f'{ns}id').text.split(':')[-1]
                video_title = entry.find(f'{ns}title').text
                video_url = entry.find(f'{ns}link').attrib['href']
                
                # Render'da dosya kaydı kalıcı değildir, basit kontrol:
                # Gerçek bir veritabanı olmadığı için her restartta sıfırlanabilir
                # Ama basit kullanım için yeterli.
                channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                if channel:
                    # Basit anti-spam: Son videoyu hafızada tutabiliriz ama dosya yazma Render'da geçicidir.
                    pass 
                    # Bildirim kodu buraya gelir.
    except Exception as e: print(f"Youtube Error: {e}")

# --- KOMUTLAR ---
@bot.command()
async def key(ctx):
    embed = discord.Embed(title="🔑 Sacred Key Access", description="Obtain your key below:", color=0xFFA500)
    embed.add_field(name="🔗 Key Link", value=f"[**UNLOCK SCRIPT**]({WEBSITE_URL})", inline=False)
    embed.set_image(url="https://media1.tenor.com/m/ZfL7-kC4O4EAAAAC/mahoraga-wheel.gif")
    await ctx.send(embed=embed)

@bot.command()
async def script(ctx):
    embed = discord.Embed(title="📜 Divine Technique", description="Copy the code below.", color=0x800080)
    await ctx.send(embed=embed)
    await ctx.send(f"```lua\n{SCRIPT_CODE}\n```")

@bot.command()
async def roblox(ctx, username: str):
    async with ctx.typing():
        try:
            payload = {"usernames": [username], "excludeBannedUsers": True}
            r = requests.post("https://users.roblox.com/v1/usernames/users", json=payload).json()
            if not r['data']: return await ctx.send("❌ User not found.")
            user_id = r['data'][0]['id']
            display = r['data'][0]['displayName']
            info = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
            avatar = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false").json()['data'][0]['imageUrl']
            embed = discord.Embed(title=f"{display}", url=f"https://www.roblox.com/users/{user_id}/profile", color=0x8B0000)
            embed.set_thumbnail(url=avatar)
            embed.add_field(name="ID", value=user_id)
            embed.add_field(name="Created", value=info['created'][:10])
            await ctx.send(embed=embed)
        except: await ctx.send("❌ Roblox API Error.")

@bot.command()
async def join(ctx):
    if ctx.author.voice: await ctx.author.voice.channel.connect()
    else: await ctx.send("Join VC first!")

@bot.command()
async def play(ctx, *, search):
    try:
        vc = ctx.guild.voice_client
        if not vc:
            if ctx.author.voice: vc = await ctx.author.voice.channel.connect()
            else: return await ctx.send("Join VC first!")
        async with ctx.typing():
            player = await YTDLSource.from_url(search, loop=bot.loop, stream=True)
            vc.play(player)
        await ctx.send(f"🎵 Now Playing: {player.title}")
    except: await ctx.send("❌ Error loading music.")

@bot.command()
async def leave(ctx):
    if ctx.guild.voice_client: await ctx.guild.voice_client.disconnect()

@bot.event
async def on_message(message):
    if message.author.bot: return
    if any(w in message.content.lower() for w in BAD_WORDS):
        try:
            await message.delete()
            await message.author.timeout(timedelta(minutes=1), reason="Profanity")
        except: pass
    await bot.process_commands(message)

# Web sunucusunu başlat
keep_alive()
# Token'ı environment variable'dan alıp başlat
if TOKEN:
    bot.run(TOKEN)
else:
    print("HATA: TOKEN BULUNAMADI! Render ayarlarını kontrol et.")