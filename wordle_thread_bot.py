import argparse
import discord
from datetime import datetime
import pytz
from urllib.parse import unquote as urldecode
import yaml


COMMAND_PREFIX = '!wordle'

parser = argparse.ArgumentParser(prog=COMMAND_PREFIX, add_help=False, exit_on_error=False)
subparsers = parser.add_subparsers(dest='subcommand', title='subcommands')

custom_parser = subparsers.add_parser('custom', help='Create a custom thread', add_help=False, usage='%(prog)s name [...]')
custom_parser.add_argument('name', nargs=argparse.REMAINDER)

thread_arg = {
  'dest': 'thread',
  'action': 'store',
  'help': 'Direct #thread mention or thread ID',
  'nargs': argparse.OPTIONAL
}
archive_parser = subparsers.add_parser('archive', help='Archive a thread', add_help=False)
archive_parser.add_argument(**thread_arg)

delete_parser = subparsers.add_parser('delete', help='Delete a thread', add_help=False)
delete_parser.add_argument(**thread_arg)

help_parser = subparsers.add_parser('help', help='Display help', add_help=False)
help_parser.add_argument('name', nargs=argparse.OPTIONAL, help='Command to show help for')

class BotClient(discord.Client):
  admin_ids: list = []
  timezone = datetime.now().astimezone().tzinfo

  async def on_ready(self):
    print(f'Logged in as: {self.user} | Timezone: {self.timezone}')

  async def on_message(self, message: discord.Message):
    print(f'[#{message.channel}] <@{message.author}> {message.content}')

    if message.author.bot:
      if message.author.id != self.user.id:
        return

      if message.type != discord.MessageType.thread_created:
        return

      await message.delete()
      return

    command_parts = message.content.strip().split()
    if command_parts[0] != COMMAND_PREFIX:
      return

    try:
      args = parser.parse_args(command_parts[1:])
    except Exception as e:
      await message.reply(f'Error parsing command input: {e}')
      return

    match args.subcommand:
      case 'custom' if len(args.name) == 0:
        await message.reply(custom_parser.format_usage())

      case None | 'custom':
        thread_prefix = 'wordle'
        if args.subcommand == 'custom':
          thread_prefix =  urldecode(' '.join(args.name))
        thread_prefix = thread_prefix.title()

        today = datetime.now(self.timezone).date()
        start_date = datetime(2021, 6, 19, tzinfo=self.timezone).date()
        thread_num = (today - start_date).days

        message_channel = message.channel
        if isinstance(message_channel, discord.Thread):
          message_channel = message_channel.parent

        for thread in message_channel.threads:
          if thread.archived:
            continue

          if f'{thread_prefix} {thread_num}'.lower() in thread.name.lower():
            await message.reply(f'It looks like there is already a {thread_prefix} {thread_num} thread in this channel: <#{thread.id}>')
            return

        spoiler_thread: discord.Thread = await message_channel.create_thread(
          name=f'{thread_prefix} {thread_num} ({today.strftime("%a %b %e")}) [[SPOILERS]]',
          auto_archive_duration=1440,
          type=discord.ChannelType.public_thread,
        )
        await message.channel.send(f'{thread_prefix} {thread_num} Spoiler Thread: <#{spoiler_thread.id}>')

      case 'archive' | 'delete':
        thread_id = -1
        if args.thread is None and isinstance(message.channel, discord.Thread):
          thread_id = message.channel.id
        else:
          try:
            thread_id = int(args.thread)
          except ValueError:
            thread_id = int(args.thread.replace('<', '').replace('>', '').replace('#', ''))

        if thread_id == -1:
          await message.reply('Invalid thread')
          return

        thread: discord.Thread = message.guild.get_thread(thread_id)
        if thread is None:
          archived_threads = await message.channel.archived_threads().flatten()
          for t in archived_threads:
            if t.id == thread_id:
              thread = t
              break

        if thread is None:
          await message.reply(f'Unable to find thread by ID: {thread_id}')
          print(await message.channel.archived_threads().flatten())
          return

        match args.subcommand:
          case 'archive' if thread.archived:
            await message.reply(f'Thread is already archived: <#{thread.id}>')
          case 'archive':
            await thread.edit(archived=True)
            if args.thread is not None:
              await message.reply(f'Thread archived: <#{thread.id}>')
          case 'delete' if message.author.id not in self.admin_ids:
            await message.reply('You are not authorized to delete threads')
          case 'delete':
            await thread.delete()
            if args.thread is not None:
              await message.reply('Thread deleted')

      case 'help':
        if args.name:
          await message.reply(subparsers.choices[args.name].format_help())
        else:
          await message.reply(parser.format_help())

      case _:
        await message.reply(f'Unhandled subcommand: {args.subcommand}')

  async def on_thread_join(self, thread):
    print(thread)

def main():
  config = yaml.safe_load(open('config.yaml').read())
  if 'discord_token' not in config or \
    not isinstance(config['discord_token'], str) or \
      config['discord_token'].strip() == '':
    print('ERROR: Missing or invalid discord_token in config.yaml')
    exit(1)

  if 'admin_ids' not in config or not isinstance(config['admin_ids'], list):
    print('ERROR: Missing or invalid admin_ids in config.yaml')
    exit(1)

  bot_client = BotClient()
  bot_client.admin_ids = config['admin_ids']

  if 'timezone' in config:
    try:
      bot_client.timezone = pytz.timezone(config['timezone'])
    except pytz.UnknownTimeZoneError:
      print('ERROR: Provided invalid timezone in config.yaml')
      exit(1)

  bot_client.run(config['discord_token'].strip())

if __name__ == '__main__':
  main()
