# Discord Mod Check Bot

A Discord bot that tracks moderator activity and enforces weekly message quotas. Mods or trail mods who do not meet the required activity receive strikes; after accumulating strikes, they are automatically demoted. Head mods have a higher strike threshold. Certain users can exempt members from checks using a command.

This bot works on **Render free-tier** using a minimal HTTP server to satisfy the port requirement.

---

## Features

* Tracks messages from Mods, Trail Mods, and Head Mods
* Weekly mod check every **Saturday at 01:00 UTC**
* Automatic strikes and demotion based on message quota
* Head mods require **5 strikes** before demotion
* Exemption system for authorized users
* Announces results in a specified **announcement channel**
* Sends DM to users when demoted
* JSON-based storage; no database required

---

## Setup

1. **Clone the repository**

2. **Install dependencies** for Python 3.10+

3. **Set environment variable** for your Discord bot token (`DISCORD_TOKEN`)

4. **Configure your server IDs** in `config.py`:

   * Mod Role ID
   * Trail Mod Role ID
   * Head Mod Role ID
   * Announcement Channel ID
   * Exempted Users (who can use `/exempt`)

5. **Ensure a JSON file exists** to store mod stats (initially empty).

---

## Deployment on Render Free Tier

1. Create a **Web Service** (not Worker).
2. Use **Python 3.10+** as the environment.
3. Set **Build Command** to install dependencies.
4. Set **Start Command** to run the bot.
5. The bot contains an internal HTTP server to satisfy Render’s port requirement.

---

## Commands

* `/exempt user` – Exempt a member from this week’s mod check. Only authorized users can run this command
* `/remove_exempt user` – Remove exemption

---

## Notes

* **Change all IDs** (roles, channel, exempted users) to match your server before deploying.
* Head Mods are **not exempted** by `/exempt`; they have a **higher strike limit**.
* The bot automatically resets weekly message counts after each mod check.
* JSON storage persists strikes and message counts between bot restarts.


If you want, I can also make a **one-page diagram** showing how roles, strikes, exemptions, and demotions work visually for GitHub. Do you want me to do that?
