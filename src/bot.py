import os
import discord
import psycopg2
import google.generativeai as genai

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')
DB_NAME = str(os.getenv('POSTGRES_DB'))
DB_USER = str(os.getenv('POSTGRES_USER'))
DB_PASSWORD = str(os.getenv('POSTGRES_PASSWORD'))
DB_HOST = str(os.getenv('POSTGRES_HOST'))

# Initialize gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize the client with intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Initialize connection to PSQL DB
dbconn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)

dbcur = dbconn.cursor()

async def probeGemini(prompt):
    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=200,
            temperature=2.0
        ))
    return response.text

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!g'):
        prompt = message.content[2:]
        result = await probeGemini(prompt)
        await message.channel.send(result)

# Run the client
client.run(DISCORD_API_KEY)

dbcur.close()
dbconn.close()
