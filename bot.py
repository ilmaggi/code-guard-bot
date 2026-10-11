import discord
from discord.ext import commands
import os
import re
import asyncio

# --- CONFIGURAZIONE ---
CANALE_CODICI_ID = 1558837797690015911 
CANALE_CLIP_ID = 1558121727949672532 
CANALE_AFK_ID = 1558879456066674819 

TOKEN = os.getenv("DISCORD_TOKEN")

# Dizionari per tenere traccia dei timer attivi
timer_mute = {}
afk_timer = {}  # <--- NUOVO: tiene traccia degli utenti nel canale AFK

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
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connesso come {bot.user}")

# --- LOGICA DI GESTIONE VOCALE (MUTO + AFK) ---
@bot.event
async def on_voice_state_update(member, before, after):
    
    # --- PARTE 1: Logica per il MUTO (sposta in AFK dopo 5 minuti) ---
    if after.mute or after.self_mute:
        if member.id not in timer_mute:
            print(f"Timer muto avviato per {member.name}")
            
            async def sposta_dopo_timeout():
                await asyncio.sleep(300) # 5 minuti
                if member.voice and (member.voice.mute or member.voice.self_mute):
                    afk_channel = member.guild.get_channel(CANALE_AFK_ID)
                    if afk_channel and member.voice.channel.id != CANALE_AFK_ID:
                        try:
                            await member.move_to(afk_channel, reason="Auto-move: utente mutato da oltre 5 minuti")
                            print(f"Utente {member.name} spostato in AFK.")
                        except discord.Forbidden:
                            print(f"ERRORE: Permessi insufficienti per spostare {member.name}.")
                timer_mute.pop(member.id, None)

            asyncio.create_task(sposta_dopo_timeout())
            timer_mute[member.id] = True
    else:
        if member.id in timer_mute:
            print(f"Timer muto annullato per {member.name} (smutato)")
            timer_mute.pop(member.id, None)

    # --- PARTE 2: Logica per l'AFK (disconnetti dopo 10 minuti) ---
    
    # Caso A: L'utente è APPENA ENTRATO nel canale AFK
    if after.channel and after.channel.id == CANALE_AFK_ID and before.channel != after.channel:
        if member.id not in afk_timer:
            print(f"Timer AFK avviato per {member.name} (10 minuti)")
            
            async def disconnetti_dopo_timeout():
                await asyncio.sleep(600) # 10 minuti
                # Ricontrolla se è ancora nel canale AFK
                if member.voice and member.voice.channel and member.voice.channel.id == CANALE_AFK_ID:
                    try:
                        await member.move_to(None, reason="Auto-disconnect: in AFK da oltre 10 minuti")
                        print(f"Utente {member.name} disconnesso dall'AFK.")
                    except discord.Forbidden:
                        print(f"ERRORE: Permessi insufficienti per disconnettere {member.name}.")
                afk_timer.pop(member.id, None)

            asyncio.create_task(disconnetti_dopo_timeout())
            afk_timer[member.id] = True

    # Caso B: L'utente è USCITO dal canale AFK
    elif before.channel and before.channel.id == CANALE_AFK_ID and after.channel != before.channel:
        if member.id in afk_timer:
            print(f"Timer AFK annullato per {member.name} (uscito dall'AFK)")
            afk_timer.pop(member.id, None)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == CANALE_CODICI_ID:
        if not is_probabilmente_codice(message.content):
            await message.delete()
            try:
                await message.author.send(f"⚠️ Il tuo messaggio in <#{CANALE_CODICI_ID}> è stato eliminato perché non sembra essere codice.")
            except discord.Forbidden:
                pass

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
