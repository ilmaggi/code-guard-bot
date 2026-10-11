import discord
from discord.ext import commands
import os

# --- CONFIGURAZIONE ---
# Sostituisci con l'ID del tuo canale #codici
CANALE_CODICI_ID = 1558837797690015911

# Il token del tuo bot (verrà letto da una variabile d'ambiente per sicurezza)
TOKEN = os.getenv("DISCORD_TOKEN")

# --- LOGICA DI RILEVAMENTO ---
def is_probabilmente_codice(contenuto):
    """
    Analizza il messaggio e restituisce True se sembra codice, False se sembra chiacchiera.
    """
    # 1. Blocchi di codice Discord (```)
    if contenuto.startswith("```") and contenuto.endswith("```"):
        return True
    if "`" in contenuto:  # Codice inline
        return True

    # 2. Parole chiave comuni di vari linguaggi
    keywords = [
        "def ", "class ", "import ", "from ", "function ", "const ", "let ", "var ",
        "if ", "else ", "for ", "while ", "return ", "print(", "console.log",
        "public ", "static ", "void ", "int ", "float ", "string ", "bool ",
        "<html>", "<div>", "<?php", "SELECT ", "FROM ", "WHERE ", "async ", "await "
    ]
    contenuto_lower = contenuto.lower()
    if any(kw in contenuto_lower for kw in keywords):
        return True

    # 3. Simboli e operatori tipici del codice
    simboli = ["{", "}", "(", ")", "[", "]", ";", "==", "=>", "+=", "-=", "*/", "//", "&&", "||"]
    conteggio_simboli = sum(contenuto.count(s) for s in simboli)
    if conteggio_simboli >= 3: # Se ci sono almeno 3 simboli, è probabile che sia codice
        return True

    # 4. Indentazione (spazi o tab all'inizio di una riga)
    righe = contenuto.split("\n")
    if len(righe) > 1:
        for riga in righe:
            if riga.startswith("    ") or riga.startswith("\t"):
                return True

    # 5. Se nessun indizio è stato trovato, consideralo chiacchiera
    return False

# --- CONFIGURAZIONE DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True  # Necessario per leggere il contenuto dei messaggi

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connesso come {bot.user}")

@bot.event
async def on_message(message):
    # Ignora i messaggi del bot stesso
    if message.author == bot.user:
        return

    # Controlla solo i messaggi nel canale #codici
    if message.channel.id == CANALE_CODICI_ID:
        if not is_probabilmente_codice(message.content):
            # Cancella il messaggio
            await message.delete()
            
            # Avvisa l'utente in privato
            try:
                await message.author.send(
                    f"⚠️ Il tuo messaggio in <#{CANALE_CODICI_ID}> è stato eliminato perché non sembra essere codice. "
                    "Questo canale è riservato esclusivamente alla programmazione."
                )
            except discord.Forbidden:
                # L'utente ha i DM disabilitati, non possiamo fare nulla
                pass

    # Assicurati che gli altri comandi del bot funzionino ancora
    await bot.process_commands(message)

# Avvia il bot
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Errore: Variabile d'ambiente DISCORD_TOKEN non impostata.")