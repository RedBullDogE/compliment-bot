# Compliment bot
Scheduled compliments by Telegram Bot. The project is written with aiogram + RethinkDB

This bot allows users to set a schedule for receiving compliments by days of week and specific time. Demo version can be viewed [here](https://t.me/cutie_compliment_bot) (but I'm not sure).

## Tech stack
* `Python`
* `aiogram`
* `RethinkDB` as database
* `APScheduler` as scheduler

## Issues
Using the bot can be accompanied by some issues. Some notable ones:
* The bot uses an external source (website) to get compliments. If this website is not available, the bot won't work properly.
* It is also possible to use a cache for requests to the compliment source, but it needs additional configuration.
* Time zones are not taken into account when creating a schedule. The bot uses the time zone of the server it is running on.

## Could be improved
* Support for different languages
* Support for multiple compliment sources
* Add more flexible time scheduling: with configurable minutes and more frequent complimenting (e.g. twice a day)
