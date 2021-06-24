# Compliment bot
Scheduled compliments by Telegram Bot. The project is written with aiogram + RethinkDB

This bot allows users to set a schedule for receiving compliments by days of week and specific time.

## Tech stack
* `Python`
* `aiogram`
* `RethinkDB` as database
* `aioschedule` as scheduler

## Issues
Using the bot can be accompanied by some issues. Some notable ones:
* Aioschedule sometimes duplicates messages (it's better to replece it with Celery or anything else).
* The bot uses an external source (website) to get compliments. If this website is not available, the bot won't work properly.
* It is also possible to use a cache for requests to the compliment source, but it needs additional configuration.
