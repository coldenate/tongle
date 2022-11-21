"""CopyCat cog"""

import os
import interactions
import pymongo
from models.session import Session  # pylint: disable=import-error

from models.user import PsuedoUser
from tools.conversions import dict_to_session
from tools.session_tools import get_session  # pylint: disable=import-error


pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))

database = pymongo_client.server


class SessionManager(interactions.Extension):
    """CopyCat cog to copy people's accounts!!! So scary!!!"""

    def __init__(self, client):
        self.client: interactions.Client = client

    # interactions.extension_command decorator that has an option called User that is set to User
    @interactions.extension_command(
        name="start",
        description="Start a translation session",
        options=[
            interactions.Option(
                name="user",
                description="The user you want to translate with",
                type=interactions.OptionType.USER,
                required=True,
            )
        ],
    )
    async def start_session(
        self, ctx: interactions.CommandContext, user: interactions.User
    ):
        """Begin an active session"""
        # create a new PsuedoUser
        author_user = PsuedoUser(
            ctx.author.name, ctx.author.id
        )  # the user that was sending the command
        target_user = PsuedoUser(user.username, user.id)
        # register the webhook
        await author_user.register_webhook(self.client, ctx)
        # register the database
        # user.register_db()  # DEPRECATED
        # send a message to the user
        await ctx.send(f"Session started for {author_user.name}!")
        # create session object
        session = Session(author_user, target_user, ctx.guild_id, ctx.channel_id)
        session.register_session(database=database)
        # ping the specified user that the author_user has requested to start a session with them. ask the user to type /accept_session
        await ctx.send(
            f"{user.mention}, {author_user.name} has requested to start a translation session with you! Type /accept_session to accept the session."
        )

    # @interactions.extension_command()
    # async def copycat(self, ctx):
    #     """CopyCat command to copy people's accounts!!! So scary!!!"""
    #     # first, initialize the pseudo user
    #     pseudo_user = PsuedoUser(name=ctx.author.name, user_id=ctx.author.id, agreed=True)
    #     # register the pseudo user
    #     await pseudo_user.register_webhook(self.client, ctx)
    #     pseudo_user.register_db()
    #     # send a message to the channel
    #     await ctx.send(
    #         content=f"Registered {pseudo_user.name} in {ctx.channel_id}",
    #         ephemeral=True,
    #     )
    @interactions.extension_command()
    async def accept_session(self, ctx):
        """Accept a session"""
        # get the session from the database

        session = get_session(target=ctx.author.id, database=database)
        session = dict_to_session(session)

        # check if the session exists
        if session is None:
            await ctx.send(
                "You do not have a session to accept! You can start on with /session start"
            )
            return
        # check if the session is already accepted
        if session.accepted:
            await ctx.send("This session has already been accepted!")
            return
        # accept the session
        session.accepted = True
        # register the webhook
        await session.receiver.register_webhook(self.client, ctx)
        # register the database
        # session.target_user.register_db()  # DEPRECATED
        session.sync_session(database=database)
        # send a message to the author
        await ctx.send(
            f"Session accepted for {session.receiver.name}! You can now start translating!"
        )


def setup(client):
    """Setup function for CopyCat cog"""
    SessionManager(client)
