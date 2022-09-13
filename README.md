# WordleThreadBot

A discord bot for creating daily [Wordle](https://www.nytimes.com/games/wordle/index.html) discussion spoiler threads

## How to run

First, copy `config.example.yaml` to `config.yaml` and edit with your own values.

The bot will need the follow permissions: https://discordapi.com/permissions.html#326417525760

aka

- View Channels
- Send Messages
- Send Messages in Threads
- Create Public Threads
- Manage Messages
- Manage Threads

You will also need to enable the `Message Content` privileged intent: https://support-dev.discord.com/hc/en-us/articles/4404772028055

## Bot Usage

You can create a new daily wordle thread with `/wordle`.

## Wordle-like Games

You can also create threads for Wordle-like daily games (such as [Nerdle](https://nerdlegame.com/)) using `/custom`. You can optionally provide a start date as well, if it's different from Wordle.
