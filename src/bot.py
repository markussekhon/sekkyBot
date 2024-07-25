import os
import sys
import signal
import asyncio
import psycopg2
import interactions
import google.generativeai as genai
import wordle.utils as wordlegame
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('POSTGRES_HOST')

# Initialize gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize connection to PSQL DB
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cursor = conn.cursor()

# Initialize the bot with intents
bot = interactions.Client(token=DISCORD_API_KEY)

# Initialize the scheduler
scheduler = AsyncIOScheduler()


@interactions.slash_command(
    name="gemini",
    description="Ask gemini a question!"
)
async def text_gemini(prompt):
    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=200,
            temperature=2.0
        ))
    return response.text


@bot.event()
async def on_ready():
    print(f'We have logged in as {bot.user.username}')
    scheduler.start()

@interactions.slash_command(
    name="playwordle",
    description="Play a round of Wordle",
    options=[
        interactions.SlashCommandOption(
            name="guess",
            description="Your 5-letter guess",
            type=interactions.OptionType.STRING,
            required=True,
        )
    ]
)
async def play_wordle(ctx, guess):
    if ctx.channel.name.lower() != "wordle":
        await ctx.send(content="Wordle can only be played in the #wordle channel. If there is no #wordle channel, please get an admin to make one so you can start playing! :)" ,ephemeral=True)
        return

    serverID = str(ctx.guild_id)
    discordID = str(ctx.author.id)

    if len(guess) != 5 or not guess.isalpha():
        await ctx.send(content="Invalid guess. Please enter a valid 5-letter word.", ephemeral=True)
        return

    result = await wordlegame.wordleRound(cursor, serverID, discordID, guess)

    if result == 0:
        await ctx.send(content="You've used all attempts! Play again tommorrow :D !", ephemeral=True)
    elif result == 1:
        await ctx.send(content="Congratulations! You've guessed the word correctly! The thread will now be closed.", ephemeral=True)
    elif result == 2:
        await ctx.send(content="Word isn't in the database, try again :P !", ephemeral=True)
    else:
        gamestate = result[0]
        attempts = result[1]

        feedback = ["⬛"] * 5
        for i, status in enumerate(gamestate):
            if status == 2:
                feedback[i] = "🟩"
            elif status == 1:
                feedback[i] = "🟨"

        if attempts < 6:
            await ctx.send(content=f"Your guess was {guess}.\n{''.join(feedback)}.\nYou have used {attempts} attempts so far, keep trying!\n", ephemeral=True)
        else:
            await ctx.send(content=f"Your guess was {guess}.\n{''.join(feedback)}.\nYou have run out of attempts. Try again tomorrow!", ephemeral=True)

def clear_database():
    try:
        cursor.execute("TRUNCATE wordlegames;")
        conn.commit()
        print("DB cleared at 00:00:00")
    except psycopg2.Error as e:
        print(f"An error occured during clear: {e}")
        conn.rollback()


scheduler.add_job(clear_database, CronTrigger(hour=0,minute=0))

# Define an async shutdown function
async def shutdown():
    print("Shutting down bot and scheduler...")

    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
    except Exception as e:
        print(f"Exception was raised during scheduler shutdown: {e}")

    cursor.close()
    conn.close()

    try:
        await bot.stop()
    except Exception as e:
        print(f"Exception was raised during bot shutdown: {e}")
    print("Shutdown complete.")

def handle_shutdown(signal, frame):
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        loop.run_until_complete(shutdown())
    else:
        asyncio.create_task(shutdown())
    

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# Run the bot
try:
    bot.start()
except (KeyboardInterrupt, SystemExit):
    print("Bot stopped")
finally:
    sys.exit(0)
