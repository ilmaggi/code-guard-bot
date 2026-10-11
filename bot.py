import discord
from discord.ext import commands
import os
import re
import asyncio  # Necessario per il timer

# --- CONFIGURAZIONE ---
# Inserisci qui l'ID del canale #codici
CANALE_CODICI_ID = 1558837797690015911 

# Inserisci qui l'ID del canale #clip
CANALE_CLIP_ID = 1558121727949672532 

# Inserisci qui l'ID del canale vocale AFK
CANALE_AFK_ID = 1558879456066674819  # <--- SOSTITUISCI CON L'ID REALE DEL CANALE AFK

TOKEN = os.getenv("DISCORD_TOKEN")

# Dizionario per tenere traccia dei timer attivi
timer_mute = {}

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
    if message.attachments:
        for att in message.attachments:
            if att.content_type and att.content_type.startswith(('image/', 'video/')):
                return True

    urls = re.findall(r'(https?://[^\s]+)', message.content)
    if not urls:
        return False

    media_domains = [
        'youtube.com', 'youtu.be', 'twitch.tv', 'tiktok.com', 'instagram.com', 
        'imgur.com', 'giphy.com', 'streamable.com', 'twitter.com', 'x.com',
        'tenor.com', 'reddit.com', 'vimeo.com', 'dailymotion.com'
    ]
    
    media_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.webm', '.avi', '.mkv')

    for url in urls:
        if any(domain in url.lower() for domain in media_domains):
            return True
        url_pulito = url.lower().split('?')[0]
        if url_pulito.endswith(media_exts):
            return True

    return False

# --- CONFIGURAZIONE DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # NECESSARIO per rilevare i cambiamenti vocali

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connesso come {bot.user}")

# --- LOGICA DI GESTIONE VOCALE (AFK) ---
@bot.event
async def on_voice_state_update(member, before, after):
    # 1. Controlla se l'utente è stato mutato (da server o da solo)
    if after.mute or after.self_mute:
        if member.id not in timer_mute:
            print(f"Timer avviato per {member.name} (mutato)")
            
            async def sposta_dopo_timeout():
                # Attende 1 minuto (60 secondi) - MODIFICATO PER IL TEST
                await asyncio.sleep(60) 
                
                # Ricontrolla lo stato: se è ancora mutato e in un canale vocale, spostalo
                if member.voice and (member.voice.mute or member.voice.self_mute):
                    afk_channel = member.guild.get_channel(CANALE_AFK_ID)
                    if afk_channel and member.voice.channel.id != CANALE_AFK_ID:
                        try:
                            await member.move_to(afk_channel, reason="Auto-move: utente mutato da oltre 1 minuto")
                            print(f"Utente {member.name} spostato in AFK.")
                        except discord.Forbidden:
                            print(f"ERRORE: Permessi insufficienti per spostare {member.name}.")
                
                # Rimuovi il timer dal dizionario
                timer_mute.pop(member.id, None)

            asyncio.create_task(sposta_dopo_timeout())
            timer_mute[member.id] = True

    # 2. Se l'utente NON è più mutato, annulla il timer
    else:
        if member.id in timer_mute:
            print(f"Timer annullato per {member.name} (smutato)")
            timer_mute.pop(member.id, None)

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
