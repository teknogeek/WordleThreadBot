import asyncio
from datetime import datetime
from discord import app_commands, utils, ChannelType, Client, Intents, Interaction, Message, MessageType, Object, Thread
from urllib.parse import unquote as urldecode
import yaml
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# logging
import logging
utils.setup_logging(level=logging.INFO)

# load config
config = yaml.safe_load(open("config.yaml").read())
if "discord_token" not in config or \
        not isinstance(config["discord_token"], str) or \
        config["discord_token"].strip() == "":
    logging.error("Missing or invalid discord_token in config.yaml")
    exit(1)

if "admin_role" not in config or \
        not isinstance(config["admin_role"], str) or \
        config["admin_role"].strip() == "":
    logging.error("Missing or invalid admin_role in config.yaml")
    exit(1)

intents = Intents.default()
intents.message_content = True

client = Client(intents=intents)
tree = app_commands.CommandTree(client)

timezone = datetime.now().astimezone().tzinfo

if "timezone" in config:
    try:
        timezone = ZoneInfo(config["timezone"])
    except ZoneInfoNotFoundError:
        logging.error("Provided invalid timezone in config.yaml")
        exit(1)

WORDLE_START_DATE = datetime(2021, 6, 19, tzinfo=timezone).date()

@client.event
async def on_ready():
    logging.info("Connected")

@client.event
async def on_message(msg: Message):
    # Auto delete "New Thread Created" message to prevent spoilers
    if not msg.author.bot:
        return

    if msg.author.id != client.user.id:
        return

    if msg.type != MessageType.thread_created:
        return

    logging.info(f"Deleting thread creation message ({msg.id})...")
    await msg.delete()

@tree.command(name="wordle")
async def wordle_create(interaction: Interaction):
    """Create a new wordle thread"""
    await create_game_thread(interaction, WORDLE_START_DATE, "wordle")


@tree.command(name="custom")
@app_commands.describe(name="Name of game")
@app_commands.describe(start_date="Start date for the custom game (MM/DD/YYYY)")
async def wordle_custom(interaction: Interaction, name: str, start_date: str = None):
    """Create a custom Wordle-like game thread"""
    if start_date is None:
        start_date = WORDLE_START_DATE
    else:
        start_date = datetime.strptime(
            start_date, "%m/%d/%Y").replace(tzinfo=timezone).date()

    await create_game_thread(interaction, start_date, urldecode(name))


async def create_game_thread(interaction: Interaction, start_date: datetime, prefix: str):
    prefix = prefix.title()
    today = datetime.now(timezone).date()
    thread_num = (today - start_date).days

    message_channel = interaction.channel
    if isinstance(message_channel, Thread):
        message_channel = await client.get_channel(message_channel.parent_id)

    for thread in await interaction.guild.active_threads():
        if thread.parent_id != message_channel.id:
            continue

        if f"{prefix} {thread_num}".lower() in thread.name.lower():
            await interaction.response.send_message(
                f"It looks like there is already a {prefix} {thread_num} thread in this channel: <#{thread.id}>"
            )
            return

    logging.info(f"Creating {prefix} {thread_num} thread...")
    spoiler_thread: Thread = await message_channel.create_thread(
        name=f"{prefix} {thread_num} ({today.strftime('%a %b %e')}) [[SPOILERS]]",
        auto_archive_duration=1440,
        type=ChannelType.public_thread,
    )
    await interaction.response.send_message(f"{prefix} {thread_num} Spoiler Thread: <#{spoiler_thread.id}>")


@tree.command(name="sync")
@app_commands.describe(guild_only="Sync commands to only this guild")
@app_commands.describe(guild_only="Just clear commands")
@app_commands.checks.has_role(config["admin_role"])
async def sync_command(interaction: Interaction, guild_only: bool = False, clear: bool = False):
    """Sync bot commands"""
    await interaction.response.send_message(f"Syncing to {'guild' if guild_only else 'global'}...", ephemeral=True)

    logging.info("Syncing...")
    guild = interaction.guild if guild_only else None
    if guild is not None:
        tree.clear_commands(guild=guild)
        if not clear:
            tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    logging.info("Synced")

    await interaction.edit_original_response(content="Synced.")

@sync_command.error
async def sync_error(interaction: Interaction, error: app_commands.AppCommandError):
    await interaction.followup.send(error, ephemeral=True)

async def main():
    async with client:
        await client.start(config["discord_token"].strip())

if __name__ == "__main__":
    asyncio.run(main())
