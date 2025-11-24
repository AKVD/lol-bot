import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import sys
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Add the current directory to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Intent setup
intents = discord.Intents.default()
intents.message_content = True

# Health check server (Required for Koyeb)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint for Koyeb"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'status': 'ok',
            'message': 'LoL Discord Bot is running',
            'timestamp': datetime.utcnow().isoformat(),
            'bot_ready': bot.is_ready() if 'bot' in globals() else False
        }
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

def start_health_server(port=8000):
    """Start HTTP server for Koyeb health checks"""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Health check server started on port {port}")
    return server

class LoLBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents, help_command=None)

    async def setup_hook(self):
        # Load extensions
        await self.load_extension('cogs.general')
        print("Loaded cogs.general")
        
        # Start periodic health check (prevents Koyeb sleep)
        self.keep_alive_task.start()
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Servers: {len(self.guilds)}')
        print('------')
    
    @tasks.loop(minutes=10)
    async def keep_alive_task(self):
        """Periodic self-ping to prevent Koyeb sleep (Free plan limitation)"""
        health_url = os.getenv('HEALTH_CHECK_URL')
        if health_url:
            try:
                import requests
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    print(f"Keep-alive ping successful")
            except Exception as e:
                print(f"Keep-alive ping failed: {e}")

# Create bot instance
bot = LoLBot()

# Hot reload command
@bot.tree.command(name='reload', description='Reload bot commands (Admin only)')
@app_commands.default_permissions(administrator=True)
async def reload_cogs(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        await bot.reload_extension('cogs.general')
        await interaction.followup.send("✅ Reloaded successfully!")
        print("Manual reload completed")
    except Exception as e:
        await interaction.followup.send(f"❌ Reload error: {str(e)}")
        print(f"Reload error: {e}")

# Update and reload command
@bot.tree.command(name='update', description='Update bot from git and reload (Admin only)')
@app_commands.default_permissions(administrator=True)
async def update_bot(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        # Git pull
        result = subprocess.run(
            ['git', 'pull'], 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        
        # Reload cogs
        await bot.reload_extension('cogs.general')
        
        if 'Already up to date' in output or 'Already up-to-date' in output:
            await interaction.followup.send("ℹ️ Already up to date. Reloaded anyway.")
        else:
            await interaction.followup.send(f"✅ Updated and reloaded!\n```{output[:500]}```")
        
        print(f"Update completed: {output}")
    except subprocess.TimeoutExpired:
        await interaction.followup.send("❌ Update timed out")
    except Exception as e:
        await interaction.followup.send(f"❌ Update error: {str(e)}")
        print(f"Update error: {e}")

# Health check command
@bot.tree.command(name='ping', description='Check bot status')
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")

def main():
    # Get token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set.")
        print("Create a .env file with: DISCORD_TOKEN=your_token_here")
        print("Or set environment variable: export DISCORD_TOKEN=your_token")
        return

    # Start health check server (Required for Koyeb)
    port = int(os.getenv('PORT', '8000'))
    start_health_server(port)

    print("Starting bot...")
    bot.run(token)

if __name__ == '__main__':
    main()
