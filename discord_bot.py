#!/usr/bin/env python3.11
import logging
import discord
import os
import aiohttp
import asyncio
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from discord.ext import commands
from discord.ext.commands import has_permissions
from dotenv import load_dotenv
from collections import deque
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create bot instance
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

nltk.download('vader_lexicon')

# Per-user chat history
user_chat_histories = {}

# Max history length
MAX_HISTORY_LENGTH = 10

# Bot event: Ready
@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} has connected to Discord!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    user_id = str(message.author.id)
    user_chat_histories.setdefault(user_id, deque(maxlen=MAX_HISTORY_LENGTH))
    chat_history = user_chat_histories[user_id]

    system_message = {
        "role": "system",
        "content": (
            "" # Add something here to give your bot a personality
        )
    }

    chat_history.append({"role": "user", "content": message.content})
    messages = [system_message] + list(chat_history)
    fallback_url = "http://localhost:11434/v1/chat/completions"
    fallback_model = "dolphin-phi"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(fallback_url, json={
                "model": fallback_model,
                "messages": messages,
                "max_tokens": 250,
                "temperature": 0.5,
                "max_length": 2000,
            }) as response:
                if response.status == 200:
                    reply = await response.json()
                    reply_content = reply['choices'][0]['message']['content']
                else:
                    reply_content = "Error: Unable to process the request. Please try again later."

    except Exception as e:
        logging.error(f"Fallback model request failed: {e}")
        reply_content = "Error: Unable to process the request. Please try again later."

    # Split reply into chunks if too long
    MAX_DISCORD_LENGTH = 2000  # Discord's character limit for a single message
    if len(reply_content) > MAX_DISCORD_LENGTH:
        chunks = [reply_content[i:i + MAX_DISCORD_LENGTH] for i in range(0, len(reply_content), MAX_DISCORD_LENGTH)]
    else:
        chunks = [reply_content]

    # Send each chunk
    for chunk in chunks:
        await message.channel.send(chunk)
        await asyncio.sleep(1)  # Ensure that commands are processed

    # Ensure that commands are processed
    await bot.process_commands(message)

# Ping command
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Web scrape command
@bot.command()
async def web_scrape(ctx, url):
    # Check if the url starts with http:// or https://
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url # For security reasons, use https

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await ctx.send(f"Failed to retrieve the page. Status code: {response.status}")
                    return

                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                page_text = soup.get_text()

                # Split the text into chunks of up to 1950 characters to leave room for formatting
                chunk_size = 1950
                chunks = [page_text[i:i + chunk_size] for i in range(0, len(page_text), chunk_size)]

                for idx, chunk in enumerate(chunks, start=1):
                    header = f"**Page Content (Part {idx}/{len(chunks)})**\n"
                    await ctx.send(header + chunk)

    except aiohttp.ClientError as e:
        await ctx.send(f"An error occurred: {str(e)}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")

# Clear chat history command
@bot.command()
async def clear(ctx):
    user_id = str(ctx.author.id)
    user_chat_histories[user_id] = deque(maxlen=MAX_HISTORY_LENGTH)
    await ctx.send("Your chat history has been cleared.")

@bot.command()
async def analyze(ctx, url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url  # Ensure HTTPS for security

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await ctx.send(f"Failed to retrieve the page. Status code: {response.status}")
                    return

                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                page_text = soup.get_text()

                # Sentiment Analysis
                analyzer = SentimentIntensityAnalyzer()
                sentiment_score = analyzer.polarity_scores(page_text)
                sentiment = sentiment_score['compound']

                await ctx.send(f"The sentiment of the page is `{sentiment}`.")

                # Prepare AI request
                messages = [
                    {"role": "system", "content": "Analyze the following webpage and summarize it:"},
                    {"role": "user", "content": page_text[:4000]}  # Limit to 4000 characters
                ]

                async with session.post(fallback_url, json={
                    "model": fallback_model,
                    "messages": messages,
                    "max_tokens": 250,
                    "temperature": 0.5
                }) as ai_response:
                    if ai_response.status == 200:
                        ai_data = await ai_response.json()
                        ai_response_content = ai_data['choices'][0]['message']['content']
                    else:
                        ai_response_content = "Error: AI request failed."

                # Split and send response in chunks
                MAX_DISCORD_LENGTH = 2000
                chunks = [ai_response_content[i:i + MAX_DISCORD_LENGTH] for i in range(0, len(ai_response_content), MAX_DISCORD_LENGTH)]

                for idx, chunk in enumerate(chunks, start=1):
                    header = f"**AI Analysis (Part {idx}/{len(chunks)})**\n"
                    await ctx.send(header + chunk)

    except aiohttp.ClientError as e:
        await ctx.send(f"An error occurred: {str(e)}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    # Specific error handling
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to use this command.")
    elif isinstance(error, commands.MissingRequiredFlags):
        await ctx.send("Please provide the required arguments for this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("That command does not exist.")
    elif isinstance(error, commands.CommandDisabled):
        await ctx.send("That command is disabled.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Please try again in {round(error.retry_after, 2)} seconds.")
    elif isinstance(error, commands.CommandError):
        await ctx.send(str(error) if error else "An error occurred while executing the command.")
    elif isinstance(error, commands.CommandInvocationError):
        await ctx.send(str(error) if error else "An error occurred while executing the command.")
    elif isinstance(error, commands.CommandSyntaxError):
        await ctx.send(str(error) if error else "An error occurred while executing the command.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(str(error) if error else "An error occurred while executing the command.")
    else:
        await ctx.send("An unexpected error occurred. Please try again later.")

    # Log the error with detailed context
    logging.error(f"Error in command '{ctx.command}' by {ctx.author}: {error}", exc_info=True)

# Run bot
bot.run(DISCORD_TOKEN)
