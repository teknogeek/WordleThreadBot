import discord
from datetime import datetime
import pytz
from urllib.parse import unquote as urldecode
import yaml


class BotClient(discord.Client):
  admin_ids: list = []
  timezone = datetime.now().astimezone().tzinfo

  async def on_ready(self):
    print(f'Logged in as: {self.user} | Timezone: {self.timezone}')

  async def on_message(self, message: discord.Message):
    print(f'[#{message.channel}] <@{message.author}> {message.content}')
    # print(repr(message))

    if message.author.bot:
      if message.author.id != self.user.id:
        return

      if message.type != discord.MessageType.thread_created:
        return

      await message.delete()
      return

    command_parts = message.content.strip().lower().split(' ')
    command_part_len = len(command_parts)

    if command_parts[0] != '!wordle':
      return

    if command_part_len == 1 or command_parts[1] == 'custom':
      thread_prefix = 'wordle'
      if command_part_len > 1 and command_parts[1] == 'custom':
        if command_part_len < 3:
          await message.reply('Usage: !wordle custom <name>')
          return

        thread_prefix =  urldecode(' '.join(command_parts[2:]))

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
    elif command_parts[1] in ['archive', 'delete']:
      if command_part_len != 3:
        await message.reply('Usage: !wordle <delete|archive> <#thread|thread ID>')
        return

      thread_id = -1
      try:
        thread_id = int(command_parts[2])
      except ValueError:
        thread_id = int(command_parts[2].replace('<', '').replace('>', '').replace('#', ''))

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

      if command_parts[1] == 'archive':
        if thread.archived:
          await message.reply(f'Thread is already archived: <#{thread.id}>')
          return

        await thread.edit(archived=True)
        await message.reply(f'Thread archived: <#{thread.id}>')
      elif command_parts[1] == 'delete':
        if message.author.id not in self.admin_ids:
          await message.reply('You are not authorized to delete threads')
          return

        await thread.delete()
        await message.reply('Thread deleted')
    elif command_parts[1] == 'help':
      await message.reply('\n'.join([
        '**Thread Creation**: !wordle',
        '**Thread Creation (Custom Game)**: !wordle custom <name>',
        '**Thread Management**: !wordle <delete|archive> <#thread|thread ID>'
      ]))
      return

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
