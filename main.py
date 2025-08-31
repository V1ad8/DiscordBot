import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import sys
import asyncio
from functools import wraps

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import server_manager as sm   # import your server functions

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def update_status():
    if sm.is_server_running():
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game("Server running")
        )
    else:
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Game("Server offline")
        )

async def status_watcher():
    await bot.wait_until_ready()

    while not bot.is_closed():
        await update_status()
        await asyncio.sleep(300)  # check every 5 minutes

def require_valid_environment(func):
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        manager_role = discord.utils.get(ctx.guild.roles, name="Server-Manager")
        bot_channel = discord.utils.get(ctx.guild.channels, name="bot-commands")

        # If bot-commands channel exists, enforce it
        if bot_channel is not None and ctx.channel.id != bot_channel.id:
            await ctx.message.delete()
            await ctx.send(f"⚠️ You can only use this command in {bot_channel.mention}.", delete_after=10)
            return

        if manager_role is not None and manager_role not in ctx.author.roles and not ctx.author.guild_permissions:
            await ctx.send("⚠️ You do not have permission to use this command.", delete_after=10)
            return

        await func(ctx, *args, **kwargs)
    return wrapper

@bot.event
async def on_ready():
    bot.loop.create_task(status_watcher())

@bot.command()
@require_valid_environment
async def start(ctx):
    if sm.is_server_running():
        await ctx.send("⚠️ Server is already running!")
        return

    await ctx.send("🚀 Starting the Minecraft server...")
    await sm.start_server()  # non-blocking
    await ctx.send("✅ Server started!")
    await update_status()

@bot.command()
@require_valid_environment
async def stop(ctx):
    if not sm.is_server_running():
        await ctx.send("⚠️ Server is not running.")
        return
    
    if sm.are_players_online():
        await ctx.send("⚠️ Players are still online!")
        return

    await ctx.send("🛑 Stopping the server...")
    await sm.shutdown_server()
    await ctx.send("✅ Server stopped!")
    await update_status()

@bot.command()
@require_valid_environment
async def online(ctx):
    if not sm.is_server_running():
        await ctx.send("⚠️ Server is offline.")
        return

    online_players = sm.get_online_players()
    if online_players:
        await ctx.send(f"✅ Online players: {', '.join(online_players)}")
    else:
        await ctx.send("❌ No players are currently online.")

@bot.command()
@require_valid_environment
async def shutdown(ctx):
    if sm.is_server_running():
        await stop(ctx)

        while sm.is_server_running():  # wait until server fully stops
            await asyncio.sleep(1)

    await ctx.send("🛑 Shutting down the server...")
    os.system("shutdown /s")
    await ctx.send("✅ Server is shutting down.")

@bot.command()
@require_valid_environment
async def cancel(ctx):
    await ctx.send("🛑 Cancelling shutdown...")
    os.system("shutdown /a")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)