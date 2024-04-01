import discord
from discord.ext import commands
import asyncio
import random
import string
import datetime 
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True # Enable voice state intent

bot = commands.Bot(command_prefix='/', intents=intents)

# Dictionary to store user tokens
user_tokens = {}
session_start_time = None
playing = False
# Dictionary to store users in voice channels
users_in_voice = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    global playing, session_start_time  # Declare these variables as global within the function

    if message.author == bot.user:
        return

    user_id = message.author.id
    if user_id not in user_tokens:
        user_tokens[user_id] = 0

    if message.content.lower() == "i love bk":
        if playing:
            # Calculate the time left until the current session ends
            now = datetime.datetime.now()
            elapsed = now - session_start_time
            time_left = max(33 - elapsed.total_seconds(), 0)  # Assuming a fixed session duration of 33 seconds
            response = f"{message.author.mention}, another user is at bk right now, check back soon! ({int(time_left)} sec)."
            await send_message_to_ad_spot(message.guild, response)
        else:
            playing = True
            session_start_time = datetime.datetime.now()  # Update the session start time
            await create_private_voice_channel(message.author, message)
            playing = False
            session_start_time = None  # Reset the session start time
    elif message.content.lower() == "bk balance":
        tokens = user_tokens.get(user_id, 0)
        response = f"{message.author.mention}, you have {tokens} tokens."
        await message.channel.send(response)
    elif message.content.lower() == "bk verify super fan":
        user_tokens[user_id] = 999999999
        response = f"{message.author.mention}, you have been verified as a BK super fan! You now have 999,999,999 tokens."
        await message.channel.send(response)
    elif message.content.lower() == "bk gamble":
        # 50/50 chance to double or lose all tokens
        if random.randint(0, 1) == 0:
            user_tokens[user_id] = 0
            response = f"{message.author.mention}, tough luck! You've lost all your tokens."
        else:
            user_tokens[user_id] *= 2
            response = f"{message.author.mention}, congratulations! Your tokens have been doubled to {user_tokens[user_id]}."
        await message.channel.send(response)
    elif message.content.lower() == "i hate bk":
        # Set user's tokens to -10
        user_tokens[user_id] = -10
        response = f"{message.author.mention}, your disdain for BK has been noted. You now have -10 tokens."
        await message.channel.send(response)
    else:
        if user_tokens[user_id] < 1:
            await message.delete()
            response = f"{message.author.mention}, you don't have enough tokens to send a message. Say 'I love BK' to get more tokens."
            await send_message_to_ad_spot(message.guild, response)
        else:
            user_tokens[user_id] -= 5 # Deduct 5 tokens

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    if before.channel is None and after.channel is not None:
        # User joined a voice channel
        if member.id not in users_in_voice:
            users_in_voice[member.id] = after.channel
            response = f"{member.mention} has joined {after.channel.mention} sponsored by BK!"
            await send_message_to_ad_spot(member.guild, response)
            bot.loop.create_task(update_tokens(member))
    elif before.channel is not None and after.channel is None:
        # User left a voice channel
        if member.id in users_in_voice:
            del users_in_voice[member.id]
            response = f"Thanks {member.mention} for talking with BK today! You now have {user_tokens[member.id]} tokens."
            await send_message_to_ad_spot(member.guild, response)

async def create_private_voice_channel(user, message):
    guild = user.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
        user: discord.PermissionOverwrite(read_messages=True, connect=True),
        bot.user: discord.PermissionOverwrite(read_messages=True, connect=True)
    }
    channel_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    voice_channel = await guild.create_voice_channel(channel_name, overwrites=overwrites)
    voice_client = await voice_channel.connect()

    response = f" ok prove it and join my voice call {voice_channel.mention}!"
    await send_message_to_ad_spot(message.guild, response)

    def check(member, before, after):
        return member == user and after.channel == voice_channel

    try:
        await bot.wait_for('voice_state_update', check=check, timeout=60)
        audio_number = random.randint(1, 10)
        audio_path = f"audio{audio_number}.mp3"
        voice_client.play(discord.FFmpegPCMAudio(audio_path))
        await asyncio.sleep(33) # Adjust depending on audio length
    except asyncio.TimeoutError:
        response = f"{user.mention}, you didn't join the private voice channel with BK within 60 seconds. No tokens granted."
        await send_message_to_ad_spot(user.guild, response)
        await voice_client.disconnect()
        await voice_channel.delete()
        return

    await voice_client.disconnect()
    await voice_channel.delete()
 # Prompt the user to enter the number they heard
    prompt_response = f"{user.mention}, what number did you hear?"
    await send_message_to_ad_spot(user.guild, prompt_response)

    def check_msg(m):
        # Check that the message is from the user, in the correct channel, and is a digit
        return m.author == user and m.channel == message.channel and m.content.isdigit()

    try:
        # Wait for the user's response
        msg = await bot.wait_for('message', check=check_msg, timeout=30)  # Adjust timeout as needed
        if msg.content == str(audio_number):
            # Grant tokens if the number is correct
            user_tokens[user.id] += 20  # Adjust token amount as needed
            response = f"{user.mention}, correct! You have been granted 20 tokens for correctly identifying the number. You now have {user_tokens[user.id]} tokens."
        else:
            response = f"{user.mention}, incorrect number. No tokens granted."
        await send_message_to_ad_spot(user.guild, response)
    except asyncio.TimeoutError:
        # Handle case where the user does not respond in time
        response = f"{user.mention}, you did not provide a number in time. No tokens granted."
        await send_message_to_ad_spot(user.guild, response)

async def update_tokens(member):
    while True:
        await asyncio.sleep(10)  # Wait for 1 second
        if member.id not in users_in_voice:
            # If the user is no longer being tracked, exit the loop
            break

        # Get the current voice state of the member to check their current voice channel
        current_voice_state = member.voice
        if not current_voice_state or not current_voice_state.channel:
            # If the member is not in any voice channel, remove them from tracking and break from the loop
            users_in_voice.pop(member.id, None)
            break

        if member.id in user_tokens and user_tokens[member.id] > 0:
            user_tokens[member.id] -= 1  # Deduct 1 token for each second in a voice channel
        else:
            # User's token count reached 0
            # Check if the bot is in the same voice channel as the member
            bot_in_channel = bot.user.id in [user.id for user in current_voice_state.channel.members]
            if not bot_in_channel:
                # Only disconnect the member if the bot is not in the same voice channel
                await member.move_to(None, reason="Insufficient tokens")  # Disconnect the member from the voice channel
                response = f"{member.mention}, you have been disconnected due to insufficient tokens."
                await member.send(response)
            users_in_voice.pop(member.id, None)  # Remove the member from tracking regardless of bot's presence
            break




async def send_message_to_ad_spot(guild, message):
    ad_spot_channel = discord.utils.get(guild.text_channels, name='bk-ad-spot')
    if ad_spot_channel:
        await ad_spot_channel.send(message)


bot.run('DiscordToken')
