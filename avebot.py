import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv # per i file .env
import yt_dlp as youtube_dl
import requests # per le richieste HTTP
import json
import random
import asyncio


intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!", intents=intents, description="non farebbe nulla di male")



### SALUTO ###
@bot.event
async def on_message(message):
    if message.author == bot.user:  # così non risponde a se stesso
        return
    if message.content.startswith("ciao"):  # saluta
        await message.channel.send(f"Ciao {message.author.name}! :)")
    await bot.process_commands(message)



### AFORISMA ###
def API_citazione():
    risposta = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(risposta.text)
    citazione = json_data[0]['q'] + " -" + json_data[0]['a']  # q, a, sono variabili API
    return (citazione)

@bot.command(pass_context=True, description="aforismi famosi", help="ENG - ricevi un aforisma")
async def inspire(ctx):
    await ctx.channel.send(API_citazione())



### MONETA ###
def lanciomoneta():
    moneta = ["Testa", "Croce"]
    risultato = random.choice(moneta)
    return (f"È uscita {risultato}")

@bot.command(pass_context=True, description="lancia una moneta", help="Lancia una moneta")
async def moneta(ctx):
    await ctx.channel.send(lanciomoneta())



### DADO ###
def tirodado(quantità, facce):
    tiri = "tiri: "
    somma = 0
    for i in range(0, int(quantità)):
        dado = random.randint(1, int(facce))
        tiri = f"{tiri} {str(dado)}, "
        somma = somma + int(dado)
    tiri = f"{tiri} | *totale: {str(somma)}*"
    descrizioneTiri = f"sono stati tirati {str(quantità)} dadi a {str(facce)} facce"
    return (
        descrizioneTiri,
        tiri,
    )

@bot.command(pass_context=True, description="lancia un dado", help='lancia un dado')
async def tira(ctx, quantità, facce):
    await ctx.channel.send(tirodado(quantità, facce)[0])
    await ctx.channel.send(tirodado(quantità, facce)[1])



### MUSICA ###
queue = [] # lista delle canzoni
ytdl_format_options = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True, # non stampa messaggi in console
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes
        'outtmpl': "/home/ave/avebot/music/%(id)s.%(ext)s", # dove scarica e con che nome
        'verbose': True
}

ffmpeg_options = {
    'options': '-vn'
}

@bot.command(name='p', help="Riproduce l'audio di un video YouTube")
async def play(ctx,url):
    
    if random.randint(0, 50) == 1 : 
        await ctx.send(f"Io non prendo ordini da {ctx.message.author.name}")
        return
    elif random.randint(0, 50) == 2 :
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # rickroll
    #if ctx.message.author.name=="Ave" :

    with youtube_dl.YoutubeDL(ytdl_format_options) as ytdl : 
        info = ytdl.extract_info(url, download=False) # per avere informazioni del video (senza scaricarlo)
        title = info['title']
        duration = info['duration']

    class YTDLSource(discord.PCMVolumeTransformer): # parte copiata, serve per evitare un errore con ytdl.download([url])
        def __init__(self, source, *, data, volume=0.5):
            super().__init__(source, volume)
            self.data = data
            self.title = data.get('title')
            self.url = ""

        @classmethod
        async def from_url(cls, url, *, loop=None, stream=False):
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream)) # anche qua estrae i dati senza scaricarlo
            if 'entries' in data:
                # take first item from a playlist
                data = data['entries'][0]
            filename = data['title'] if stream else ytdl.prepare_filename(data)
            return filename
    
    if duration > 1200 : # 20 min
        await ctx.send(f"{title} è troppo lungo (durata: {duration} secondi)")
        return

    try :
        server = ctx.message.guild
        voice_channel = server.voice_client
        queue.append((url, title, duration))

        if not ctx.voice_client.is_playing():
            while queue:  # se la lista è vuota da "False", altrimenti "True"
                url, title, duration = queue.pop(0)  # prende (e "spacchetta") il primo elemento della lista e lo rimuove da essa

                async with ctx.typing():
                    #ytdl.download([url])  # scarica l'audio (non usata perchè andava in errore con video lunghi)
                    filename = await YTDLSource.from_url(url, loop=bot.loop) # scarica l'audio usando la classe creata prima
                    voice_channel.play(discord.FFmpegPCMAudio(filename))  # riproduce l'audio
                await ctx.send(f"**In riproduzione:** {title} (durata: {duration} secondi)")
                await asyncio.sleep(duration + 5)

    except AttributeError: # per: 'NoneType' object has no attribute 'is_playing'
        await ctx.send(f"Devo prima entrare nel canale (usa: *!entra*)")

    except Exception as errore:
        await ctx.send(f"**Errore:** {errore}")

@bot.command(name='entra', help='Fa entrare AveBot')
async def entra(ctx):
    if not ctx.message.author.voice:
        await ctx.send("devi connetterti ad un canale vocale {}".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='esci', help='Fa uscire AveBot')
async def esci(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()

@bot.command(name='pausa', help='Pausa la riproduzione')
async def pausa(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("Al momento non c'è nulla in riproduzione")
    
@bot.command(name='continua', help='Continua la riprooduzione')
async def continua(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("Non c'è nessuna traccia in sospeso")
    
@bot.command(name='stop', help='Ferma la riproduzione')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("Al momento non c'è nulla in riproduzione")



### SUONO UTENTE ###
@bot.event
async def on_voice_state_update(member, before, after):
    cartella  = r"/home/ave/avebot/sound"
    with os.scandir(cartella) as lista_suoni_utente : # scansione cartella
        for file_suono in lista_suoni_utente :
            if member.name == file_suono.name[:-4] :
                if before.channel is None and after.channel is not None: # l'user si è unito ad un canale vocale
                    channel = after.channel
                    if bot.voice_clients: # controlla se il bot è già in un client vocale (voice_clients è un lista)
                        for voice_channel in bot.voice_clients:
                            if voice_channel.channel == channel:  
                                await voice_channel.play(discord.FFmpegPCMAudio(r"/home/ave/avebot/sound/" + file_suono.name))



### FONDAMENTALI ###
@bot.event
async def on_ready(): # i.e. appena si avvia
    print(f"\n{bot.user} è online\n")
    for guild in bot.guilds:
        print(f'Attivo in: {guild.name} (Membri: {guild.member_count})')
        #print('Active in {}\t Member Count : {}'.format( guild.name, guild.member_count))


load_dotenv() # prende la variabile API dal file .env
DISCORD_TOKEN = os.getenv("discord_token")
if __name__ == "__main__" : # se chiamato/importato da un'altra script non funziona
    bot.run(DISCORD_TOKEN)