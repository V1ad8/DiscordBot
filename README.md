# **Discord Bot to Manage Minecraft Servers**

## **Overview**
This project allows you to **manage a Minecraft Java Edition server** via a **Discord bot**.  
It includes:
- `server_manager.py` – API to start, manage, and stop the Minecraft server.
- `main.py` – Discord bot to execute commands from your Discord server.

> **Tested on Windows 10 & 11**  
> Requires **Python 3.9+** and **Java (for Minecraft server)**.

---

## **Features**
- Start and stop the Minecraft server remotely.
- View who is online.
- Automatic server shutdown when inactive.
- Optional PC shutdown feature.
- Role-based command restrictions.

---

## **Quick Start**
```bash
# Clone the repository
git clone <your-repo-url>
cd <your-repo-directory>

# Install dependencies
pip install -r requirements.txt

# Configure .env with your Discord bot token
echo "DISCORD_TOKEN=your-bot-token" > .env

# Start the Discord bot
python main.py
```

## Setup Instructions

### Set up the Minecraft Server

Follow [Mojang's official guide](https://help.minecraft.net/hc/en-us/articles/360058525452-How-to-Setup-a-Minecraft-Java-Edition-Server).

Then, place these scripts in the same directory as your Minecraft server files.

### Configure `server_manager.py`

| Variable             | Description                                                         |
| -------------------- | ------------------------------------------------------------------- |
| `rejoin_timer`       | Seconds to wait before stopping the server after last player leaves |
| `first_join_timer`   | Seconds to wait for first player to join before auto-stopping       |
| `sending_timer`      | Delay between sending commands to the server                        |
| `process_exit_steps` | Steps before forcefully killing process on failure                  |
| `waiting_step`       | Time between checking server output                                 |
| `server_jar`         | Name of the Minecraft `.jar` file                                   |
| `server_directory`   | Path to the server directory                                        |
| `ram`                | Amount of RAM for the server (e.g., `"2G"`)                         |
| `gui`                | Enable/disable GUI (usually `false`)                                |

The Server Manager can be run via:

```bash
python run_server.py
```

### Set up the Discord Bot

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Get a discoed token. [Here](https://www.youtube.com/watch?v=YD_N6Ffoojw), it starts at 5:39.

2. Set the token in `.env`

3. Start the bot:

```bash
python main.py
```

## Discord Bot Behavior

If a role named Server-Manager exists, only members with this role or admins can use commands.

If a channel named bot-commands exists, the bot only responds there and deletes commands elsewhere.

## Commands

| Command     | Action                             |
| ----------- | ---------------------------------- |
| `!start`    | Start the Minecraft server         |
| `!stop`     | Stop the Minecraft server          |
| `!online`   | Show server status and players     |
| `!shutdown` | Shut down the PC (⚠ use carefully) |
| `!cancel`   | Cancel PC shutdown                 |

Notes

Ensure Java is installed and available in your system PATH.

The shutdown feature will turn off the PC, so use it with caution.

The bot and Minecraft server should ideally run on a dedicated machine.
