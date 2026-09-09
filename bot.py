import os

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv


# Load the .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


# Discord intents
intents = discord.Intents.default()


# Create the bot
class RapidRank(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")



bot = RapidRank()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("RapidRank is online!")

def get_rating_role(guild, rating):
    """
    Find the highest RapidRank role the player qualifies for.

    Roles should be named like:
    ♟️ 800
    ♟️ 1000
    ♟️ 1200
    ♟️ 1400
    """

    eligible_roles = []

    for role in guild.roles:

        # Only look at roles starting with our prefix
        if not role.name.startswith("♟️ "):
            continue

        # Try to get the number from the role name
        try:
            threshold = int(role.name.replace("♟️ ", ""))

        except ValueError:
            continue

        # Player qualifies for this role
        if rating >= threshold:
            eligible_roles.append((threshold, role))

    # No role matched
    if not eligible_roles:
        return None

    # Return the highest qualifying threshold
    eligible_roles.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return eligible_roles[0][1]


# Get a player's Chess.com Rapid rating
async def get_rapid_rating(username):

    url = f"https://api.chess.com/pub/player/{username}/stats"

    # Chess.com asks API clients to identify themselves
    headers = {
        "User-Agent": "RapidRank Discord Bot"
    }

    async with aiohttp.ClientSession(headers=headers) as session:

        async with session.get(url) as response:

            # Player doesn't exist
            if response.status == 404:
                return None

            # Something else went wrong
            if response.status != 200:
                return None

            data = await response.json()

            # Get Rapid information
            rapid = data.get("chess_rapid")

            if rapid is None:
                return None

            # Get their current Rapid rating
            last_game = rapid.get("last")

            if last_game is None:
                return None

            return last_game.get("rating")

# /chess command
@bot.tree.command(
    name="chess",
    description="Look up a Chess.com Rapid rating."
)
async def chess(
    interaction: discord.Interaction,
    username: str
):

    await interaction.response.defer()

    # Get the player's Rapid rating
    rating = await get_rapid_rating(username)

    if rating is None:
        await interaction.followup.send(
            f"❌ I couldn't find a Rapid rating for `{username}`."
        )
        return

    # Find the appropriate role dynamically
    role = get_rating_role(
        interaction.guild,
        rating
    )

    if role is None:
        await interaction.followup.send(
            f"♟️ **{username}** has a Rapid rating of "
            f"**{rating}**, but there isn't a RapidRank role "
            f"for that rating yet."
        )
        return

    # Remove existing RapidRank roles
    for old_role in interaction.user.roles:

        if (
            old_role.name.startswith("♟️ ")
            and old_role != role
        ):
            try:
                threshold = int(
                    old_role.name.replace("♟️ ", "")
                )

                # It's a RapidRank role
                await interaction.user.remove_roles(
                    old_role
                )

            except ValueError:
                pass

    # Give the new role
    await interaction.user.add_roles(role)

    # Tell the user
    await interaction.followup.send(
        f"♟️ **{username}**\n"
        f"⚡ Rapid rating: **{rating}**\n"
        f"🏆 Rank: {role.mention}"
    )