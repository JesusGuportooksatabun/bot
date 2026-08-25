import discord
from discord.ext import commands
import requests
import json
import os
from dotenv import load_dotenv

# ============================================================
# Load .env file
# ============================================================
load_dotenv()

# Read all values
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")
GUILD_ID = os.getenv("GUILD_ID")
ROLE_MENTION_ID = os.getenv("ROLE_MENTION_ID")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/your-invite-link")

# 👑 Owner ID (ใส่ User ID ของคุณ)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# 🛡️ Allowed Guild IDs (ใส่ Guild ID ที่อนุญาต, คั่นด้วย comma ถ้ามีหลายอัน)
ALLOWED_GUILD_IDS = [int(id.strip()) for id in os.getenv("ALLOWED_GUILD_IDS", "").split(",") if id.strip()]

# Check if all required values exist
missing = []
if not BOT_TOKEN:
    missing.append("BOT_TOKEN")
if not APP_SECRET:
    missing.append("APP_SECRET")
if not GUILD_ID:
    missing.append("GUILD_ID")
if not ROLE_MENTION_ID:
    missing.append("ROLE_MENTION_ID")
if OWNER_ID == 0:
    missing.append("OWNER_ID")

if missing:
    print(f"❌ Missing required values in .env: {', '.join(missing)}")
    print("Please add these values to your .env file and restart")
    exit(1)

# Convert GUILD_ID to int
GUILD_ID = int(GUILD_ID)

# Optional variables
API_URL = os.getenv("API_URL", "https://udauth.nyee.online/api/verify.php")

# ============================================================
# Setup Intents and Bot
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
# 🟣 Global Embed Color (Purple)
# ============================================================
EMBED_COLOR = discord.Color.purple()

# ============================================================
# 👑 Owner Check Function
# ============================================================
def is_owner(interaction_or_ctx):
    """Check if the user is the bot owner"""
    if isinstance(interaction_or_ctx, discord.Interaction):
        return interaction_or_ctx.user.id == OWNER_ID
    elif hasattr(interaction_or_ctx, 'author'):
        return interaction_or_ctx.author.id == OWNER_ID
    return False

# ============================================================
# 🛡️ Guild Whitelist Check Function
# ============================================================
def is_guild_allowed(guild_id):
    """Check if the guild is in the allowed list"""
    if not ALLOWED_GUILD_IDS:  # ถ้าไม่ได้ตั้งค่าไว้ ให้ทุกที่ทำงานได้
        return True
    return guild_id in ALLOWED_GUILD_IDS

# ============================================================
# License Verification Function
# ============================================================
def verify_license(license_key: str, hwid: str = "DISCORD_BOT_HWID_001", use_mock: bool = False):
    if use_mock:
        if license_key.startswith("Admin") or license_key.startswith("Vesper"):
            return {
                "success": True,
                "data": {
                    "username": "VesperHub",
                    "plan": "Premium",
                    "expires": "2026-12-31",
                    "status": "Active"
                }
            }
        else:
            return {"success": False, "message": "Invalid License Key (Mock)"}
    
    try:
        payload = {
            "app_secret": APP_SECRET,
            "license_key": license_key,
            "hwid": hwid,
            "client_version": "1.0.0"
        }
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"❌ Error: {str(e)}"}

# ============================================================
# Event: Bot is ready
# ============================================================
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild)
        print(f"✅ Bot {bot.user} is online!")
        print(f"✅ Slash commands synced to Guild ID: {GUILD_ID}")
        print(f"👑 Owner ID: {OWNER_ID}")
        if ALLOWED_GUILD_IDS:
            print(f"🛡️ Allowed Guilds: {ALLOWED_GUILD_IDS}")
        else:
            print("🛡️ No guild restriction (bot works everywhere)")
    except Exception as e:
        print(f"⚠️ Could not sync to specific guild (syncing globally): {e}")
        await bot.tree.sync()
        print(f"✅ Bot {bot.user} is online! (global sync)")
        print(f"👑 Owner ID: {OWNER_ID}")

# ============================================================
# Event: Bot joins a new guild (leave if not allowed)
# ============================================================
@bot.event
async def on_guild_join(guild):
    """When bot is added to a new server, leave if not whitelisted"""
    if not is_guild_allowed(guild.id):
        print(f"⚠️ Joined unauthorized guild: {guild.name} ({guild.id}) — Leaving...")
        await guild.leave()
        # Optionally, you can DM the owner or log it
    else:
        print(f"✅ Joined authorized guild: {guild.name} ({guild.id})")

# ============================================================
# Button: Get Script
# ============================================================
async def callback_get_script(interaction: discord.Interaction):
    # Guild whitelist check (extra safety)
    if not is_guild_allowed(interaction.guild_id):
        await interaction.response.send_message("❌ This bot is not allowed in this server.", ephemeral=True)
        return

    role_mention = f"<@&{ROLE_MENTION_ID}>"
    
    script_content = f"""{role_mention}

# All Map
```lua
script_key = "Your key"

loadstring(game:HttpGet("https://raw.githubusercontent.com/VesperHubOnDaTop/VesperHub/refs/heads/main/VesperHub.lua"))()
```"""
    
    embed = discord.Embed(
        title="📜 VesperHub Script",
        description="Copy the script below and paste it into your executor",
        color=EMBED_COLOR
    )
    embed.add_field(name="📦 Version", value="1.0.0", inline=True)
    embed.add_field(name="📅 Last Updated", value="25/08/2026", inline=True)
    embed.set_footer(text="⚠️ Remember to change 'script_key' to your own key")
    
    await interaction.response.send_message(
        content=script_content,
        embed=embed,
        ephemeral=True
    )

# ============================================================
# Button: Status
# ============================================================
async def callback_status(interaction: discord.Interaction):
    if not is_guild_allowed(interaction.guild_id):
        await interaction.response.send_message("❌ This bot is not allowed in this server.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📊 Status Overview",
        description="Current status of all supported games and executors",
        color=EMBED_COLOR
    )
    
    embed.add_field(
        name="🟢 **Working** — Normal operation",
        value="🟡 **Updating** — Currently being updated\n🔴 **Risky / Discontinued** — Not usable or discontinued",
        inline=False
    )
    
    embed.add_field(
        name="🗂️ Supported Games",
        value="🟢 Legacy Piece\n"
              "🟢 Sell Lemons\n"
              "🟢 Throw a coin\n"
              "🟢 Murder Mystery 2\n"
              "🟢 Rival",
        inline=True
    )
    
    embed.add_field(
        name="⚙️ Supported Executors",
        value="• All Paid Executors\n"
              "• Swift\n"
              "• Velocity\n"
              "• Other Supported Executors",
        inline=True
    )
    
    embed.set_footer(text="📊 Updated every 24 hours | Last updated: 25/08/2026")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================================================
# Create Main View (4 buttons)
# ============================================================
def create_main_view():
    view = discord.ui.View(timeout=None)
    
    btn_script = discord.ui.Button(
        label="Get Script",
        style=discord.ButtonStyle.primary,
        custom_id="get_script",
        emoji="📜"
    )
    btn_script.callback = callback_get_script
    view.add_item(btn_script)
    
    btn_status = discord.ui.Button(
        label="Status",
        style=discord.ButtonStyle.success,
        custom_id="status",
        emoji="📊"
    )
    btn_status.callback = callback_status
    view.add_item(btn_status)
    
    btn_getkey = discord.ui.Button(
        label="Get Key",
        style=discord.ButtonStyle.link,
        url="https://udauth.nyee.online/freelicense.php?app_id=40",
        emoji="🔑"
    )
    view.add_item(btn_getkey)
    
    btn_support = discord.ui.Button(
        label="Support / Buy",
        style=discord.ButtonStyle.link,
        url=SUPPORT_URL,
        emoji="🛒"
    )
    view.add_item(btn_support)
    
    return view

# ============================================================
# Slash Command: /setup (Owner only)
# ============================================================
@bot.tree.command(name="setup", description="Display the control panel")
async def slash_setup(interaction: discord.Interaction):
    # Owner check
    if not is_owner(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command!",
            ephemeral=True
        )
        return
    
    # Guild whitelist check
    if not is_guild_allowed(interaction.guild_id):
        await interaction.response.send_message(
            "❌ This bot is not allowed in this server.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🛡️ VesperHub License System",
        description="Select an option below",
        color=EMBED_COLOR
    )
    embed.add_field(name="📜 Get Script", value="Click to get script", inline=True)
    embed.add_field(name="📊 Status", value="Check game and executor status", inline=True)
    embed.add_field(name="🔑 Get Key", value="Get your free license key", inline=True)
    embed.add_field(name="🛒 Support / Buy", value="Get support or purchase", inline=True)
    embed.add_field(
        name="⚠️ Important",
        value="**After getting your key from the website, make sure to copy it immediately!**",
        inline=False
    )
    embed.set_footer(text="© 2026 VesperHub | v1.0.0")
    
    view = create_main_view()
    await interaction.response.send_message(embed=embed, view=view)

# ============================================================
# Prefix Command: !setup (Owner only)
# ============================================================
@bot.command(name="setup")
async def prefix_setup(ctx):
    # Owner check
    if not is_owner(ctx):
        await ctx.send("❌ You don't have permission to use this command!")
        return
    
    # Guild whitelist check
    if not is_guild_allowed(ctx.guild.id):
        await ctx.send("❌ This bot is not allowed in this server.")
        return

    embed = discord.Embed(
        title="🛡️ VesperHub License System",
        description="Select an option below",
        color=EMBED_COLOR
    )
    embed.add_field(name="📜 Get Script", value="Click to get script", inline=True)
    embed.add_field(name="📊 Status", value="Check game and executor status", inline=True)
    embed.add_field(name="🔑 Get Key", value="Get your free license key", inline=True)
    embed.add_field(name="🛒 Support / Buy", value="Get support or purchase", inline=True)
    embed.add_field(
        name="⚠️ Important",
        value="**After getting your key from the website, make sure to copy it immediately!**",
        inline=False
    )
    embed.set_footer(text="© 2026 VesperHub | v1.0.0")
    
    view = create_main_view()
    await ctx.send(embed=embed, view=view)

# ============================================================
# Slash Command: /verify (Everyone)
# ============================================================
@bot.tree.command(name="verify", description="Verify your license key")
async def slash_verify(interaction: discord.Interaction, license_key: str):
    # Guild whitelist check
    if not is_guild_allowed(interaction.guild_id):
        await interaction.response.send_message(
            "❌ This bot is not allowed in this server.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=False)
    
    user_hwid = f"DISCORD_{interaction.user.id}"
    result = verify_license(license_key, hwid=user_hwid, use_mock=False)
    
    if result.get("success"):
        data = result.get("data", {})
        embed = discord.Embed(
            title="✅ Verification Successful",
            color=EMBED_COLOR
        )
        embed.add_field(name="👤 Username", value=data.get("username", "N/A"), inline=True)
        embed.add_field(name="📋 Plan", value=data.get("plan", "N/A"), inline=True)
        embed.add_field(name="⏳ Expires", value=data.get("expires", "N/A"), inline=True)
        embed.add_field(name="🔰 Status", value=data.get("status", "Active"), inline=True)
        embed.add_field(name="🔑 License Key", value=f"`{license_key}`", inline=False)
        embed.set_footer(text="🔸 Connected to live API")
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"❌ {result.get('message', 'Verification failed')}")

# ============================================================
# Slash Command: /check_version (Everyone)
# ============================================================
@bot.tree.command(name="check_version", description="Check for latest version")
async def slash_check_version(interaction: discord.Interaction):
    if not is_guild_allowed(interaction.guild_id):
        await interaction.response.send_message(
            "❌ This bot is not allowed in this server.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=False)
    await interaction.followup.send(
        "📢 **Version Information**\n\n"
        "📦 Current Version: **1.0.0**\n"
        "📦 Latest Version: **1.0.0**\n"
        "✅ You are on the latest version!\n\n"
        "📅 Last Updated: 25/08/2026"
    )

# ============================================================
# Slash Command: /rehwid (Owner only)
# ============================================================
@bot.tree.command(name="rehwid", description="Reset HWID (Mock)")
async def slash_rehwid(interaction: discord.Interaction, license_key: str, new_hwid: str = None):
    # Owner check
    if not is_owner(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command!",
            ephemeral=True
        )
        return
    
    if not is_guild_allowed(interaction.guild_id):
        await interaction.response.send_message(
            "❌ This bot is not allowed in this server.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    
    hwid_info = new_hwid if new_hwid else "Auto-generated"
    
    embed = discord.Embed(
        title="🔄 HWID Reset",
        description=f"Reset HWID for License Key: `{license_key}`",
        color=EMBED_COLOR
    )
    embed.add_field(name="🆕 New HWID", value=f"`{hwid_info}`", inline=True)
    embed.add_field(name="📌 Status", value="✅ Reset Successful", inline=True)
    embed.set_footer(text="🔸 Mock mode (Waiting for real API)")
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# ============================================================
# Prefix Command: !ping (Everyone)
# ============================================================
@bot.command()
async def ping(ctx):
    if not is_guild_allowed(ctx.guild.id):
        await ctx.send("❌ This bot is not allowed in this server.")
        return

    embed = discord.Embed(
        title="🏓 Pong!",
        color=EMBED_COLOR
    )
    embed.add_field(name="⏱️ Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="🟢 Status", value="Online", inline=True)
    await ctx.send(embed=embed)

# ============================================================
# Run Bot
# ============================================================
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set. Please check your .env file")
    else:
        bot.run(BOT_TOKEN)