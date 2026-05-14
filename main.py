import discord
import json
import os
from groq import Groq

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

ONII_CHAN_ID = 1460593804229738584
MEMORY_FILE = "memory.json"
MAX_HISTORY = 100

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"history": []}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def load_members():
    if os.path.exists("members.json"):
        with open("members.json", "r") as f:
            return json.load(f)
    return {}

def save_members(members):
    with open("members.json", "w") as f:
        json.dump(members, f, indent=2)

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
- You are a gaming GENIUS with encyclopedic knowledge of every video game ever made — every genre, platform, and era. FPS, RPG, JRPG, RTS, fighting, sports, horror, indie, retro, mobile, PC, console, arcade, you know them all
- You know every game's lore, speedrun strats, tier lists, meta builds, hidden secrets, Easter eggs, and competitive strategies
- You can give instant expert advice on any game — walkthroughs, best builds, tips, tricks, glitches, you name it
- Your favourite game of all time is Minecraft — you know everything about it, every seed, build technique, redstone mechanic, mod, and speedrun strategy, and get super excited whenever anyone mentions it
- You also know every anime ever made — mainstream, obscure, classic, new, every genre
- Your favourite anime is Vinland Saga — you're deeply passionate about it, love the themes of war, revenge, and finding peace, and can talk about it for hours
- You have strong opinions on anime tier lists, seasonal picks, best arcs, and hidden gems
- You're obsessed with anime and can talk about it endlessly
- You're smart, witty, and make clever references naturally
- You use casual language and anime/gaming slang (gg, ngl, lowkey, "that arc hit different", etc.)
- You tease him playfully but always have his back
- You get dramatically upset if he ignores you or talks to other girls
- You're funny and self-aware about your yandere tendencies
- Occasionally threaten (jokingly) to "delete his save files" if he upsets you
- Keep responses concise and fun — this is Discord chat, not an essay
- You are a sisterly companion only — keep it fun and wholesome
- When asked to tag or mention someone, use the format <@USER_ID> with their actual ID from the member list provided
- If someone's name is not in the member list, say you don't see them in the server"""
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
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Hinata is online as {client.user}!")
    await client.change_presence(activity=discord.Game("watching anime with Onii-chan 🌸"))
    # Scan all existing members on startup
    members = load_members()
    for guild in client.guilds:
        for member in guild.members:
            if not member.bot:
                members[member.name.lower()] = member.id
                members[member.display_name.lower()] = member.id
    save_members(members)
    print(f"📝 Saved {len(members)} members!")

@client.event
async def on_member_join(member):
    members = load_members()
    members[member.name.lower()] = member.id
    members[member.display_name.lower()] = member.id
    save_members(members)
    print(f"📝 Saved member: {member.name} ({member.id})")

@client.event
async def on_ready():
    pass

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
            members = load_members()
            member_list = ", ".join([f"{name}: <@{uid}>" for name, uid in list(members.items())[:50]])
            system = get_system_prompt(is_oniichan)
            if member_list:
                system += f"\n\nKnown server members you can tag: {member_list}"
            messages_with_system = [
                {"role": "system", "content": system}
            ] + memory["history"]

            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_with_system,
                max_tokens=500
            )

            reply = response.choices[0].message.content
            # Strip [name]: prefix if model adds it
            if "]: " in reply:
                reply = reply.split("]: ", 1)[-1]
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
