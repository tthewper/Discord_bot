import os
import time  # ✅ Added import
import random
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from threading import Thread

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot
bot = commands.Bot(command_prefix='!', intents=intents)
client = discord.Client(intents=intents)

# Token and Channel
DISCORD_TOKEN = os.environ["TOKEN"]
CHANNEL_ID = 1375060747754668138  # Replace this with your actual channel ID

# Web server to keep bot alive
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Scheduled group reminder
async def send_group_reminder():
    await bot.wait_until_ready()  # ✅ Ensures bot is ready before accessing channels
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("@everyone Reminder: We meet today!")
    else:
        print(f"[Error] Could not find channel with ID {CHANNEL_ID}")

# Start scheduler
scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # Schedule: First and third Wednesday at 9 AM
    scheduler.add_job(send_group_reminder, CronTrigger(day='1-7', day_of_week='wed', hour=9, minute=0))
    scheduler.add_job(send_group_reminder, CronTrigger(day='15-21', day_of_week='wed', hour=9, minute=0))
    scheduler.start()

# Cooldown tracker for auto-support messages
cooldown_tracker = {}
COOLDOWN_SECONDS = 600

trigger_keywords = [
    "suicidal", "hopeless", "worthless", "don't want to be here",
    "can't go on", "ending it", "give up", "hate myself", "kill myself",
    "end it", "off myself", "no use", "no point", "no reason", "no hope", "no future"
]

auto_support_message = (
    "💙 Hey, it sounds like you're going through something really heavy.\n"
    "Please know you're not alone. If you're in immediate danger, reach out to someone you trust, "
    "contact a mental health professional, or call a support line:\n\n"
    "**📞 Trans Lifeline:** 877-565-8860\n"
    "**💬 Crisis Chat:** https://chat.988lifeline.org/\n\n"
    "You matter. We're glad you're here. 🫂"
)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    user_id = message.author.id
    now = time.time()

    if any(keyword in content for keyword in trigger_keywords):
        last = cooldown_tracker.get(user_id, 0)
        if now - last >= COOLDOWN_SECONDS:
            try:
                await message.channel.send(auto_support_message)
                cooldown_tracker[user_id] = now
            except discord.Forbidden:
                print("Missing permission to send support message.")
        else:
            print(f"Cooldown active for {message.author.name}")

    await bot.process_commands(message)

@bot.command()
async def resources(ctx):
    response = (
        "**🌈 LGBTQ+ Support Resources**\n\n"
        "**National Resources:**\n"
        "- 🧠 [Trans Lifeline](https://translifeline.org/): Peer support and crisis line run by trans people.\n"
        "- 💬 [The Trevor Project](https://www.thetrevorproject.org/): Crisis support for LGBTQ+ youth.\n"
        "- 🏥 [Planned Parenthood](https://www.plannedparenthood.org/): Gender-affirming healthcare and info.\n"
        "- 📚 [Gender Spectrum](https://www.genderspectrum.org/): Youth-focused education and family resources.\n"
        "- 🌍 [Informed Consent Map](https://tinyurl.com/4mwpm892): Find gender-affirming providers by location.\n"
        "- 📖 [Name & Gender Marker Guide](https://transequality.org/documents): Legal docs by state (U.S.).\n\n"
        "**New Jersey & Bergen County:**\n"
        "- 🧠 [Equality Mental Health](https://equalitymentalhealth.com/): LGBTQ+ affirming therapy & groups.\n"
        "- 🏳️‍🌈 [Bergen County LGBTQ+ Alliance](https://www.bergencountylgbtq.org/): Local advocacy & events.\n"
        "- 🏥 [Bergen New Bridge Medical Center](https://www.newbridgehealth.org/health-services/lgbtq-health/): Affirming care & services.\n"
        "- 🎓 [Bergen Community College Resources](https://bergen.edu/student-life/virtual-lgbtq-center/lgbtq-center-resources/): Campus support.\n"
        "- 🏳️‍⚧️ [PFLAG Bergen County](https://www.pflagnj.org/): Family & ally support.\n"
        "- 🏠 [West Bergen Rainbow Resources](https://westbergen.org/lgbtq-services-rainbow-resources/): Youth support (ages 16–20).\n"
        "- 📞 [Bergen County LGBTQ+ Office](https://www.co.bergen.nj.us/division-of-office-of-lgbtq-services/office-of-lgbtq-services-and-resources): County-wide services.\n"
        "- 🎉 [Club Feathers](https://clubfeathers.com/): Longstanding LGBTQ+ bar & venue in River Edge, NJ.\n"
    )
    await ctx.send(response)

import random


@bot.command(name="help")
async def help_command(ctx):
    response = (
        "**📌 Available Commands:**\n\n"
        "`!resources` – Lists national and local LGBTQ+ support services.\n"
        "`!legalhelp` – Provides legal help for trans folks in New Jersey.\n"
        "`!journal` – Creates your own private journaling channel. Only you and the bot can see it.\n"
        "`!gender` - Get a random gender identity. \n"
        "`!help` – Shows this list of available commands.\n\n"
        "💡 You can use these anytime, in any channel the bot has access to."
    )
    await ctx.send(response)

# Journal system commands

# Store confirmed delete requests temporarily
pending_deletions = {}

@bot.command()
async def journal(ctx):
    guild = ctx.guild
    user = ctx.author
    channel_name = f"journal-{user.name.lower().replace(' ', '-')}"

    # Check if journal already exists
    for channel in guild.text_channels:
        if channel.name == channel_name and channel.overwrites_for(user).view_channel:
            await ctx.send(f"{user.mention} you already have a journal: {channel.mention}")
            return

    # Set permissions for complete privacy
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_messages=True
        )
    }

    
    # Create the channel
    channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        topic="Private journal – only visible to you"
    )

    await ctx.send(f"{user.mention} your private journal has been created: {channel.mention}")
    await channel.send(
        f"Hi {user.mention}, this is your private journal."
        "Everything you write here is only visible to you.\n\n"
        "You can use `!journalhelp` to see all journal commands including `!clearjournal` to wipe your messages and `!deletejournal` to remove the channel.\n"
        "📓 Want a journal prompt? Type `!prompt` "

    )

@bot.command()
async def clearjournal(ctx):
    channel = ctx.channel
    user = ctx.author

    if not channel.name.startswith("journal-"):
        await ctx.send("This command can only be used in your journal channel.")
        return

    def is_user_message(m):
        return m.author == user

    deleted = await channel.purge(limit=1000, check=is_user_message)
    await ctx.send(f"{user.mention} your journal has been cleared ({len(deleted)} messages deleted).", delete_after=10)

@bot.command()
async def deletejournal(ctx):
    channel = ctx.channel
    user = ctx.author

    if not channel.name.startswith("journal-"):
        await ctx.send("This command can only be used in your journal channel.")
        return

    pending_deletions[user.id] = channel.id
    await ctx.send(
        f"{user.mention} are you sure you want to delete this journal? "
        "Type `!confirmdelete` within 60 seconds to confirm."
    )

@bot.command()
async def confirmdelete(ctx):
    user = ctx.author
    channel = ctx.channel

    # Check if user has requested deletion
    if pending_deletions.get(user.id) != channel.id:
        await ctx.send("There is no pending delete request for you in this channel.")
        return

    del pending_deletions[user.id]
    await ctx.send(f"{user.mention} deleting your journal...", delete_after=3)
    await channel.delete()

@bot.command()
async def prompt(ctx):
    # Only allow command in journal channels
    if not ctx.channel.name.startswith("journal-"):
        await ctx.send(f"{ctx.author.mention} this command can only be used in your private journal channel.")
        return

    try:
        with open("prompts.txt", "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        await ctx.send("Prompt list not found. Please upload `prompts.txt` to use this feature.")
        return

    if not prompts:
        await ctx.send("The prompt list is empty!")
        return

    import random
    chosen = random.choice(prompts)

    await ctx.send(f"📝 **Journaling Prompt:**\n{chosen}")

@bot.command()
async def journalhelp(ctx):
    # Restrict to journal channels only
    if not ctx.channel.name.startswith("journal-"):
        await ctx.send(f"{ctx.author.mention} this command can only be used in your private journal channel.")
        return

    response = (
        "**📓 Journal Commands:**\n"
        "`!prompt` – Receive a reflective journaling prompt in this channel.\n"
        "`!affirmation` - Receive an affirmation in this channel. \n"
        "`!clearjournal` – Delete all your messages from your journal.\n"
        "`!deletejournal` – Start the process to delete this journal channel.\n"
        "`!confirmdelete` – Confirms permanent deletion of this journal.\n"
        "`!journalhelp` – Shows this list of journal commands. \n"
        "💡 These commands only work here in your private journal. Take your time, you're safe here."
    )
    await ctx.send(response)

@bot.command()
async def affirmation(ctx):
    # Only allow in journal channels
    if not ctx.channel.name.startswith("journal-"):
        await ctx.send(f"{ctx.author.mention} this command can only be used in your private journal channel.")
        return

    try:
        with open("affirmations.txt", "r", encoding="utf-8") as f:
            affirmations = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        await ctx.send("Affirmation list not found. Please upload `affirmations.txt`.")
        return

    if not affirmations:
        await ctx.send("The affirmation list is empty!")
        return

    import random
    chosen = random.choice(affirmations)

    await ctx.send(f"💖 **Affirmation:**\n{chosen}")

@bot.command()
async def gender(ctx):
    try:
        with open("gender.txt", "r", encoding="utf-8") as f:
            genders = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        await ctx.send("⚠️ `gender.txt` file not found! Please upload one to use this command.")
        return

    if not genders:
        await ctx.send("⚠️ The gender list is empty!")
        return

    import random
    chosen = random.choice(genders)
    await ctx.send(f"🧃 **Your gender today is:** {chosen}")

@bot.command()
async def legalhelp(ctx):
    response = (
        "**⚖️ Legal Help for Trans Folks in New Jersey**\n\n"
        "**📄 Name & Gender Marker Changes:**\n"
        "- 🏛️ [NJ Courts Name Change Instructions](https://www.njcourts.gov/self-help/name-change/name-change-adults): Step-by-step PDF for adult name changes.\n"
        "- 🧾 [Trans Equality – NJ Legal Proctections](https://www.nj.gov/transgender/legal-protections/): Covers the legal rights of trans folks in NJ.\n"
        "- 💳 [NJ MVC Gender Marker Policy](https://www.nj.gov/transgender/name-changes/drivers-license-gender-change.shtml): Allows 'M', 'F', or 'X' on your license/ID without medical documentation.\n\n"
        "**💼 Free Legal Support & Clinics:**\n"
        "- ⚖️ [Garden State Equality](https://www.gardenstateequality.org/): Advocacy org that can help with legal referrals.\n"
        "- 🧑‍⚖️ [Volunteer Lawyers for Justice NJ](https://www.vljnj.org/): Offers free legal assistance for name changes and civil matters.\n"
        "- 🏳️‍🌈 [LGBT Bar Association of Greater NY](https://www.lgbtbarny.org/): May connect you with trans-affirming legal support in the tri-state area.\n\n"
    )
    await ctx.send(response)

# Keep bot alive and run it
keep_alive()
client.run(DISCORD_TOKEN)
