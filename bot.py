import os
import discord
import google.generativeai as genai

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')

# Initialize gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


# Initialize the client with intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def probeGemini(prompt):
    response = await model.generate_content_async(prompt)
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
