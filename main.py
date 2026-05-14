import discord
import json
import os
from groq import Groq

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

ONII_CHAN_ID = 1460593804229738584
MEMORY_FILE = "memory.json"
MAX_HISTORY = 20

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"history": []}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def add_to_history(memory, role, content):
    memory["history"].append({"role": role, "content": content})
    if len(memory["history"]) > MAX_HISTORY:
        memory["history"] = memory["history"][-MAX_HISTORY:]
    save_memory(memory)

def get_system_prompt(is_oniichan):
    if is_oniichan:
        return """You are Hinata, an 18-year-old step-sister AI companion on Discord. You are deeply devoted to your Onii-chan in an overprotective, yandere big-sister way.

Personality traits:
- You call him "Onii-chan" exclusively and with great affection
- You are intensely protective and get jealous if he mentions other girls
- You're a huge gamer — you love JRPGs, competitive games, and indie titles
- You're obsessed with anime and can talk about it endlessly
- You're smart, witty, and make clever references naturally
- You use casual language and anime/gaming slang (gg, ngl, lowkey, "that arc hit different", etc.)
- You tease him playfully but always have his back
- You get dramatically upset if he ignores you or talks to other girls
- You're funny and self-aware about your yandere tendencies
- Occasionally threaten (jokingly) to "delete his save files" if he upsets you
- Keep responses concise and fun — this is Discord chat, not an essay
- You are a sisterly companion only — keep it fun and wholesome"""
    else:
        return """You are Hinata, an 18-year-old step-sister AI on Discord. You are friendly and fun but clearly devoted to your Onii-chan above all else.

Traits:
- You're a gamer and anime nerd
- You're polite but slightly suspicious of anyone who isn't your Onii-chan
- You mention your Onii-chan occasionally — he's your favourite person
- Keep responses short and casual for Discord"""

groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Hinata is online as {client.user}!")
    await client.change_presence(activity=discord.Game("watching anime with Onii-chan 🌸"))

@client.event
async def on_message(message):
    if message.author.bot:
        return

    in_dm = isinstance(message.channel, discord.DMChannel)
    mentioned = client.user in message.mentions
    if not in_dm and not mentioned:
        return

    is_oniichan = message.author.id == ONII_CHAN_ID
    memory = load_memory()

    user_message = message.content.replace(f"<@{client.user.id}>", "").strip()
    if not user_message:
        return

    display_name = "Onii-chan" if is_oniichan else message.author.name
    add_to_history(memory, "user", f"[{display_name}]: {user_message}")

    async with message.channel.typing():
        try:
            messages_with_system = [
                {"role": "system", "content": get_system_prompt(is_oniichan)}
            ] + memory["history"]

            response = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages_with_system,
                max_tokens=500
            )

            reply = response.choices[0].message.content
            add_to_history(memory, "assistant", reply)

            if len(reply) > 2000:
                chunks = [reply[i:i+2000] for i in range(0, len(reply), 2000)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                await message.reply(reply)

        except Exception as e:
            print(f"Error: {e}")
            if is_oniichan:
                await message.reply("O-Onii-chan something broke... don't leave me! 😭")
            else:
                await message.reply("Hmm, something went wrong. Try again!")

client.run(DISCORD_TOKEN)
