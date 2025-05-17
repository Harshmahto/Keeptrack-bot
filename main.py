import discord
from discord.ext import commands
from datetime import datetime
import os
from dotenv import load_dotenv
from keep_alive import keep_alive
from zoneinfo import ZoneInfo
IST = ZoneInfo("Asia/Kolkata")

# Load token from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")

keep_alive()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

vc_times = {}        # user_id -> join datetime
log_channels = {}    # guild_id -> channel_id


@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def setlogchannel(ctx):
    """Set this channel as the VC log channel."""
    log_channels[ctx.guild.id] = ctx.channel.id
    await ctx.send(f"✅ Voice log channel set to {ctx.channel.mention}")


@bot.event
async def on_voice_state_update(member, before, after):
    guild_id = member.guild.id
    log_channel_id = log_channels.get(guild_id)
    
    if not log_channel_id:
        return  # log channel not set

    log_channel = bot.get_channel(log_channel_id)
    if not log_channel:
        return

    user_id = member.id

    if before.channel is None and after.channel is not None:
        # Joined VC
        join_time = datetime.now(IST)
        vc_times[user_id] = join_time
        await log_channel.send(
            f"🔵 {member.display_name} joined **{after.channel.name}** at `{join_time.strftime('%I:%M:%S %p IST')}`"
        )

    elif before.channel is not None and after.channel is None:
        # Left VC
        join_time = vc_times.pop(user_id, None)
        if join_time:
            leave_time = datetime.now(IST)
            duration = leave_time - join_time
            seconds = int(duration.total_seconds())
            formatted = f"{seconds//3600}h {(seconds%3600)//60}m {seconds%60}s"
            await log_channel.send(
                f"🔴 {member.display_name} left **{before.channel.name}** after `{formatted}`"
            )
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        # User switched voice channels
        join_time = vc_times.get(user_id, datetime.now(IST))
        leave_time = datetime.now(IST)
        duration = leave_time - join_time
        seconds = int(duration.total_seconds())
        formatted = f"{seconds//3600}h {(seconds%3600)//60}m {seconds%60}s"
        await log_channel.send(
            f"🔁 {member.display_name} switched from **{before.channel.name}** to **{after.channel.name}** after `{formatted}`"
        )
        # Update join time for new VC
        vc_times[user_id] = leave_time


# Run the bot
if __name__ == "__main__":
    if TOKEN:
        print("🔍 Token loaded: Yes")
        bot.run(TOKEN)
    else:
        print("❌ Token not found in .env")
