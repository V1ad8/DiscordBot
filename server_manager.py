import subprocess
import asyncio
import re
from datetime import datetime
from colorama import Fore, Style
import msvcrt

# Variables
rejoin_timer = 300              # seconds to wait before shutdown after last player leaves
first_join_timer = 600          # seconds to wait for first player to join
sending_timer = 2               # seconds to wait between sending commands
process_exit_steps = 20         # steps to wait before forcefully killing process
waiting_step = 0.5              # seconds to wait between checks

# Server directory
server_directory = "C:/Users/KIDS/Desktop/Server"
ram = "7500M"
server_jar = "forgeserver.jar"
gui = False

# Track players
online_players = set()
shutdown_scheduled = False

# Tasks
pre_join_timer = None
monitor_task = None
input_task = None

# Process
process = None

def is_server_running():
    global process
    return process is not None and process.poll() is None

def get_online_players():
    global online_players
    return online_players

def are_players_online():
    global online_players
    return True if online_players else False

async def start_server():
    global process, pre_join_timer, monitor_task, waiting_step, input_task

    if is_server_running():
        log("Server already running.", "warning")
        return

    process = subprocess.Popen(
        [
            'java',
            f'-Xmx{ram}',
            f'-Xms{ram}',
            '-jar',
            server_jar,
            'gui' if gui else 'nogui'
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=server_directory
    )

    log("Minecraft server starting...", "check")

    pattern_done = re.compile(r'Done \(([\d.]+)s\)')
    pattern_error = re.compile(r"java\.io\.IOException: The process cannot access the file because another process has locked a portion of the file")

    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, process.stdout.readline)
        
        if not line:
            if process.poll() is not None:
                log("Server has stopped.", "break")
                return
            await asyncio.sleep(waiting_step)
            continue

        line = line.strip()

        if (match := pattern_done.search(line)):
            log(f"Server done loading in {match.group(1)}s", "check")
            input_task = asyncio.create_task(read_user_input())
            break
                
        if (match := pattern_error.search(line)):
            log(f"Server file error detected; PC restart required.", "warning")
            break

    pre_join_timer = asyncio.create_task(wait_for_first_join(first_join_timer))
    monitor_task = asyncio.create_task(monitor_server_output())

def log (message, type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")

    char = 'i'
    color = Fore.WHITE
    match type:
        case "warning":
            char = '!'
            color = Fore.YELLOW
        case "break":
            char = 'X'
            color = Fore.RED
        case "check":
            char = '✓'
            color = Fore.BLUE
        case "join":
            char = '+'
            color = Fore.GREEN
        case "leave":
            char = '-'
            color = Fore.RED
        case "send":
            char = '>'
            color = Fore.MAGENTA

    print(f"[{timestamp}] {color}[{char}]{Style.RESET_ALL} {message}")

async def wait_for_first_join(timeout_seconds):
    global monitor_task

    # Wait for first player to join; shutdown if timeout expires.
    try:
        await asyncio.sleep(timeout_seconds)

        if are_players_online():
            log("First player joined before timeout — pre-join timer finished.")
            return

        log(f"No players joined for {timeout_seconds/60:.0f} minutes. Stopping script.", "warning")
        asyncio.create_task(shutdown_server())
    except asyncio.CancelledError:
        if monitor_task and not monitor_task.done():
            log("First player joined — pre-join timer cancelled.")
            raise

async def monitor_server_output():
    global process, pre_join_timer, online_players, waiting_step, rejoin_timer, shutdown_pc, input_task

    pattern_join = re.compile(r'\]: (\w+) joined the game')
    pattern_leave = re.compile(r'\]: (\w+) left the game')
    pattern_delay = re.compile(r"Can't keep up!.*Running (\d+)ms")

    loop = asyncio.get_event_loop()

    while True:
        line = await loop.run_in_executor(None, process.stdout.readline)
        
        if not line:
            if process.poll() is not None:
                log("Server has stopped.", "break")
                return
            await asyncio.sleep(waiting_step)
            continue

        line = line.strip()

        if (match := pattern_join.search(line)):
            player = match.group(1)
            online_players.add(player)
            log(f"{player} joined the game; Online now: {', '.join(online_players)}", "join")
            if pre_join_timer and not pre_join_timer.done():
                pre_join_timer.cancel()
            continue

        if (match := pattern_leave.search(line)):
            player = match.group(1)
            online_players.discard(player)

            if are_players_online():
                log(f"{player} left the game; Still online: {', '.join(online_players)}", "leave")
            else:
                log(f"{player} left the game; No one online", "leave")
                log("No players online — scheduling shutdown...", "warning")
                asyncio.create_task(shutdown_server(rejoin_timer))
            continue

        if (match := pattern_delay.search(line)):
            ms_behind = int(match.group(1))
            s_behind = ms_behind / 1000
            log(f"Server lagging behind by ({s_behind:.2f} s)", "warning")
            continue

async def read_user_input():
    buffer = ""
    while True:
        try:
            if msvcrt.kbhit():
                c = msvcrt.getwch()
                
                if c == "\r":  # Enter pressed
                    print()  # move to next line
                    command = buffer
                    buffer = ""
                    await send_command(command)
                elif c == "\b":  # Backspace
                    buffer = buffer[:-1]
                    # Move cursor back, overwrite, move cursor back again
                    print("\b \b", end="", flush=True)
                else:
                    buffer += c
                    print(c, end="", flush=True)  # echo character
            await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            return

async def send_command(cmd):
    global process

    if process.poll() is not None or process.stdin.closed:
        log(f"Skipping send_command('{cmd}') — process is not running.", "warning")
        return

    try:
        log(f"Sending '{cmd}'...", "send")
        process.stdin.write(f"{cmd}\n")
        process.stdin.flush()
    except Exception as e:
        log(f"Failed to send command '{cmd}': {e}", "warning")
        return

    await asyncio.sleep(sending_timer)

async def shutdown_server(wait_time=0):
    global process, online_players, process_exit_steps, waiting_step, shutdown_scheduled, input_task, monitor_task, pre_join_timer

    if not is_server_running():
        log("Server is not running.", "warning")
        return

    if shutdown_scheduled:
        log("Shutdown already in progress.", "warning")
        return

    shutdown_scheduled = True

    try:
        await asyncio.sleep(wait_time)
    except asyncio.CancelledError:
        log("Shutdown cancelled.", "warning")
        shutdown_scheduled = False
        return

    if are_players_online():
        log("Shutdown aborted — players are still online.", "warning")
        shutdown_scheduled = False
        return

    # Try to stop gracefully
    await send_command("save-all")
    await send_command("stop")

    # Wait for process to exit
    for _ in range(process_exit_steps):
        if process.poll() is not None:
            log("Server process exited cleanly.", "check")
            break
        await asyncio.sleep(waiting_step)

    # If still alive, force kill
    if process.poll() is None:
        log("Server did not exit, forcing kill...", "warning")
        try:
            process.kill()
            log("Server process killed.", "warning")
        except Exception as e:
            log(f"Failed to kill process: {e}", "warning")

    # Cancel tasks
    if monitor_task and not monitor_task.done():
        monitor_task.cancel()
    if input_task and not input_task.done():
        input_task.cancel()
    if pre_join_timer and not pre_join_timer.done():
        pre_join_timer.cancel()

    shutdown_scheduled = False

async def run():
    global monitor_task

    await start_server()

    try:
        await monitor_task
    except asyncio.CancelledError:
        log("Script was cancelled. Cleaning up...")
        await shutdown_server()
