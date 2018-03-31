# telegram-chat-eater

A bot that will delete Telegram group chat messages after a two-week period.

Requires a config file `config.json`, in the format:

```
{
    "API_TOKEN": "your telegram bot api token",
    "CHAT_ID": your telegram chat ID (int)
}
```