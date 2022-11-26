"""A group of event listeners that handle housekeeping tasks.i.e.: removing dead sessions from the Database, and cleaning out a channel's webhooks."""

import asyncio
import os
import interactions

import pymongo

from models.user import User  # pylint: disable=import-error

pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))
# get the database
database = pymongo_client.server

# setup a extension that has an event listener that is called when the bot receives a command
class Housekeeping(interactions.Extension):
    """Extension class for housekeeping tasks"""

    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_listener()  # type: ignore
    async def on_command(self, ctx: interactions.CommandContext) -> None:
        """Event listener that is called when a command is received"""
        # check if the message author is registered in the server's webhoooks

        # get channel's webhooks
        print("getting channel's webhooks")
        webhooks = await ctx.channel.get_webhooks()

        duplicates = []
        for webhook in webhooks:
            if ctx.author.user.username == webhook.name:
                duplicates.append(webhook)
        if len(duplicates) > 1:
            print("found duplicates")
            while len(duplicates) > 1:
                for duplicate in duplicates:
                    print("deleting duplicate")
                    await duplicate.delete()
                    # TODO: refactor this comprenhension inside an iteration
                    # to be more safe :)
                    # I can't get to it now
                    # (I think I am just being lazy)
                    duplicates.remove(duplicate)
                    break
        temp_user = User(discord_user=ctx.author.user)  # type: ignore
        presence_in_database = temp_user.search_db()
        # if not found in database, register them
        if not presence_in_database:
            print("not found in database")
            temp_user.register_db()
            # m = await ctx.channel.send(
            #     f"Hey <@{ctx.author.user.id}>, you have not registered a preferred language!\n***Simply run `/settings preferred_language`***",
            # )
            # delete this message after 20 seconds
            # await asyncio.sleep(20)
            # await m.delete()
        elif presence_in_database:
            # update the user
            temp_user.update_db()


def setup(client):
    """Setup the housekeeping extension."""
    Housekeeping(client)
    print("Housekeeping extension loaded.")
    