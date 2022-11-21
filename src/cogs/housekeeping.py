"""A group of event listeners that handle housekeeping tasks.i.e.: removing dead sessions from the Database, and cleaning out a channel's webhooks."""

import interactions
from pprint import pprint

# setup a extension that has an event listener that is called when the bot receives a command
class Housekeeping(interactions.Extension):
    """Extension class for housekeeping tasks"""

    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_listener()  # type: ignore
    async def on_command(self, ctx: interactions.CommandContext):
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
                    duplicates.remove(duplicate)
                    break


def setup(client):
    """Setup the housekeeping extension."""
    Housekeeping(client)
    print("Housekeeping extension loaded.")
