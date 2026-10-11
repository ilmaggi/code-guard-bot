import discord
from discord.ext import commands
import os
import re

# --- CONFIGURAZIONE ---
# Inserisci qui l'ID del canale #codici
CANALE_CODICI_ID = 1558837797690015911 

# Inserisci qui l'ID del canale #clip
CANALE_CLIP_ID = 1558121727949672532 

TOKEN = os.getenv("DISCORD_TOKEN")

# --- LOGICA PER #CODICI ---
def is_probabilmente_codice(contenuto):
    if contenuto.startswith("```") and contenuto.endswith("```"): return True
    if "`" in contenuto: return True
    keywords = ["def ", "class ", "import ", "from ", "function ", "const ", "let ", "var ", "if ", "else ", "for ", "while ", "return ", "print(", "console.log", "public ", "static ", "void ", "int ", "float ", "string ", "bool ", "<html>", "<div>", "<?php", "SELECT ", "FROM ", "WHERE ", "async ", "await "]
    if any(kw in contenuto.lower() for kw in keywords): return True
    simboli = ["{", "}", "(", ")", "[", "]", ";", "==", "=>", "+=", "-=", "*/", "//", "&&", "||"]
    if sum(contenuto.count(s) for s in simboli) >= 3: return True
    righe = contenuto.split("\n")
    if len(righe) > 1 and any(r.startswith("    ") or r.startswith("\t") for r in righe): return True
    return False

# --- LOGICA PER #CLIP ---
def is_media_link(message):
    # 1. Controlla se ci sono allegati (file caricati direttamente)
    if message.attachments:
        for att in message.attachments:
            if att.content_type and att.content_type.startswith(('image/', 'video/')):
                return True

    # 2. Controlla se ci sono link nel testo
    urls = re.findall(r'(https?://[^\s]+)', message.content)
    if not urls:
        return False

    # Domini comuni di video/immagini
    media_domains = [
        'youtube.com', 'youtu.be', 'twitch.tv', 'tiktok.com', 'instagram.com', 
        'imgur.com', 'giphy.com', 'streamable.com', 'twitter.com', 'x.com',
        'tenor.com', 'reddit.com', 'vimeo.com', 'dailymotion.com'
    ]
    
    # Estensioni di file multimediali
    media_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.webm', '.avi', '.mkv')

    for url in urls:
        # Controlla il dominio
        if any(domain in url.lower() for domain in media_domains):
            return True
        # Controlla l'estensione del file (rimuovendo eventuali parametri GET)
        url_pulito = url.lower().split('?')[0]
        if url_pulito.endswith(media_exts):
            return True

    return False

# --- CONFIGURAZIONE DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connesso come {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Logica per il canale #codici
    if message.channel.id == CANALE_CODICI_ID:
        if not is_probabilmente_codice(message.content):
            await message.delete()
            try:
                await message.author.send(f"⚠️ Il tuo messaggio in <#{CANALE_CODICI_ID}> è stato eliminato perché non sembra essere codice.")
            except discord.Forbidden:
                pass

    # Logica per il canale #clip
    if message.channel.id == CANALE_CLIP_ID:
        if not is_media_link(message):
            await message.delete()
            try:
                await message.author.send(f"⚠️ Il tuo messaggio in <#{CANALE_CLIP_ID}> è stato eliminato perché non contiene un video o un'immagine valida.")
            except discord.Forbidden:
                pass

    await bot.process_commands(message)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Errore: Variabile d'ambiente DISCORD_TOKEN non impostata.")
