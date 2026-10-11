import os
import staypresent

# Avvia un server web leggero in background per Render
staypresent.web.json({"status": "running"})

# Avvia il tuo bot, passando la porta assegnata da Render
staypresent.run(
    "bot.py",
    port=int(os.getenv("PORT", 8080)),
)