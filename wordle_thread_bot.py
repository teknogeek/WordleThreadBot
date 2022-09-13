import interactions
from datetime import datetime
import pytz
from urllib.parse import unquote as urldecode
import yaml

# start
config = yaml.safe_load(open('config.yaml').read())
if 'discord_token' not in config or \
  not isinstance(config['discord_token'], str) or \
    config['discord_token'].strip() == '':
  print('ERROR: Missing or invalid discord_token in config.yaml')
  exit(1)

if 'guild_id' not in config or not isinstance(config['guild_id'], int):
  print('ERROR: Missing guild_id config.yaml')
  exit(1)

bot = interactions.Client(
  token=config['discord_token'].strip(),
  default_scope=config['guild_id']
)

timezone = datetime.now().astimezone().tzinfo

if 'timezone' in config:
  try:
    timezone = pytz.timezone(config['timezone'])
  except pytz.UnknownTimeZoneError:
    print('ERROR: Provided invalid timezone in config.yaml')
    exit(1)

WORDLE_START_DATE = datetime(2021, 6, 19, tzinfo=timezone).date()

@bot.event
async def on_start():
  print(f"[+] Connected | Timezone: {timezone}")

# auto delete "New Thread Created" message to prevent spoilers
@bot.event
async def on_message_create(msg):
  if msg.author.id != bot.me.id:
    return

  if msg.type != interactions.MessageType.THREAD_CREATED:
    return

  print('[+] Deleting thread creation message...')
  await msg.delete()


@bot.command(name="wordle")
async def wordle_create(ctx: interactions.CommandContext):
  """Create a new wordle thread"""
  await create_game_thread(ctx, WORDLE_START_DATE, "wordle")

@bot.command(
  name="custom",
  options=[
    interactions.Option(
      name="name",
      description="Name of game",
      type=interactions.OptionType.STRING,
      required=True,
    ),
    interactions.Option(
      name="start_date",
      description="Start date for the custom game (MM/DD/YYYY)",
      type=interactions.OptionType.STRING,
      required=False,
    ),
  ],
)
async def wordle_custom(ctx: interactions.CommandContext, name: str, start_date: str = None):
  """Create a custom Wordle-like game thread"""
  if start_date is None:
    start_date = WORDLE_START_DATE
  else:
    start_date = datetime.strptime(start_date, "%m/%d/%Y").replace(tzinfo=timezone).date()

  await create_game_thread(ctx, start_date, urldecode(name))

async def create_game_thread(ctx: interactions.CommandContext, start_date, prefix: str):
  prefix = prefix.title()
  today = datetime.now(timezone).date()
  thread_num = (today - start_date).days

  message_channel = ctx.channel
  if isinstance(message_channel, interactions.Thread):
    message_channel = await ctx.client.get_channel(message_channel.parent_id)

  for thread in await ctx.guild.get_all_active_threads():
    if thread.parent_id != message_channel.id:
      continue

    if f'{prefix} {thread_num}'.lower() in thread.name.lower():
      await ctx.send(f'It looks like there is already a {prefix} {thread_num} thread in this channel: <#{thread.id}>')
      return

  print(f'[+] Creating {prefix} {thread_num} thread...')
  spoiler_thread: interactions.Thread = await message_channel.create_thread(
    name=f'{prefix} {thread_num} ({today.strftime("%a %b %e")}) [[SPOILERS]]',
    auto_archive_duration=1440,
    type=interactions.ChannelType.GUILD_PUBLIC_THREAD,
  )

  await ctx.send(f'{prefix} {thread_num} Spoiler Thread: <#{spoiler_thread.id}>')

bot.start()
