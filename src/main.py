"""
Entry point for the application script. Special thanks to the
boilerplate for helping me get started. :)
"""
import os
import sys

import interactions
from dotenv import load_dotenv
from interactions import MISSING
from interactions.ext.wait_for import setup
import pymongo
from config import DEV_GUILD

load_dotenv()


# TODO: add a check to see if the database cannot connect


# Instantiate environment variables
TOKEN = None
try:
    if not (TOKEN := os.environ.get("TOKEN")):
        TOKEN = None
    DEV_GUILD = os.environ.get("DEV_GUILD")
    if not DEV_GUILD or (DEV_GUILD := int(DEV_GUILD)):
        DEV_GUILD = MISSING
except TypeError:
    pass
finally:
    if TOKEN is None:
        print("TOKEN variable not set. Cannot continue")
        sys.exit(1)

client = interactions.Client(
    token=TOKEN,
    presence=interactions.ClientPresence(
        activities=[
            interactions.PresenceActivity(
                type=interactions.PresenceActivityType.LISTENING,
                name="polyglots around the world!!",
            )
        ],
        status=interactions.StatusType.ONLINE,
    ),
    disable_sync=False,
    default_scope=DEV_GUILD,
)
# Connect to the pymongo database


"""Connect to the database"""
# connect to the pymongo database using the environment variables
pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))
# get the database
database = pymongo_client.server


# setup(client)

# BEGIN on_ready
@client.event
async def on_ready():
    """Called when bot is ready to receive interactions"""
    print("Logged in")


# BEGIN cogs_dynamic_loader
# Fill this array with Python files in /cogs.
# This omits __init__.py, template.py, and excludes files without a py file extension
cogs = [
    module[:-3]
    for module in os.listdir(f"{os.path.dirname(__file__)}/cogs")
    if module not in ("__init__.py", "template.py") and module[-3:] == ".py"
]

for cog in cogs:
    try:
        client.load("cogs." + cog)
    except interactions.api.error.LibraryException:
        _ = f"Could not load cog: {cog}"
        print(_)

# END cogs_dynamic_loader


client.start()
