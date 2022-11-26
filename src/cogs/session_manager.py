"""CopyCat cog"""

import os
import interactions
import pymongo
from deep_translator import GoogleTranslator
from models.session import Session  # pylint: disable=import-error
from datetime import datetime, timedelta
from models.user import User


pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))

database = pymongo_client.server


class SessionManager(interactions.Extension):
    """CopyCat cog to copy people's accounts!!! So scary!!!"""

    def __init__(self, client):
        self.client: interactions.Client = client

    # interactions.extension_command decorator that has an option called User that is set to User
    @interactions.extension_command(name="session")
    async def session(self, ctx: interactions.CommandContext) -> None:
        """Base command for session"""

    @session.subcommand(
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
        # author_user = User(
        #     ctx.author.name, ctx.author.id, discord_user=ctx.author.user
        # )  # the user that was sending the command
        # target_user = User(
        #     user.username, user.id, discord_user=user
        # )  # the user that was selected

        # get the users from the database
        # TODO: Handle if the user doesn't exist in the database
        author_user = User(discord_user=ctx.author.user)
        target_user = User(discord_user=user)
        author_user.search_db()
        target_user.search_db()

        # register the webhook
        # check if the user already has a webhook
        for webhook in await ctx.channel.get_webhooks():
            if ctx.author.user.username == webhook.name:
                # check if the webhook exists as a session in the database
                session_as_doc = database.sessions.find_one(
                    {"initiator.user_id": int(ctx.author.id)}
                )
                if session_as_doc:
                    # if so, check if it expired or not
                    session = Session()
                    if session.check_if_expired(session_as_doc):
                        await webhook.delete()
                        database.sessions.delete_one(
                            {"initiator.user_id": int(ctx.author.id)}
                        )
                        # an expired session was found, so the webhook was deleted and the document was deleted
                        continue
                    elif session.check_if_expired(session_as_doc) is False:
                        await ctx.send(
                            ephemeral=True,
                            content="You already have an active session. Please end it before starting a new one.",
                        )
                        return

        await author_user.register_webhook(self.client, ctx.channel)

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

    @session.subcommand()
    async def accept_session(self, ctx):
        """Accept a session"""
        # get the session from the database
        # TODO: Handle multiple sessions that can be accepted.
        try:
            session = Session()
            session.get_session_acceptor(target=ctx.author.id, database=database)

        except TypeError:
            await ctx.send(
                "You do not have a session to accept! You can start on with /session start"
            )
            return
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
        await session.receiver.register_webhook(self.client, ctx.channel)
        # register the database
        # session.target_user.register_db()  # DEPRECATED
        session.sync_session(database=database)
        # send a message to the author
        await ctx.send(
            f"Session accepted for {session.receiver.name}! You can now start translating!"
        )

    @interactions.extension_listener()  # type: ignore
    async def on_message_create(self, ctx: interactions.Message) -> None:
        """The listener for intercepting messages. Following these algorithmic steps:
        1. Check if the author is in a session as a receiver or an initiator
        2. if so, assign the message content to original_message
        3. get the session from the database
        4. if the session is accepted, get the other user's preferred language and translate the message to that language
        5. get the webhook of the author
        6. send the translated message to the channel using that webhook
        """
        # ignore if the message is from a bot
        if ctx.author.bot:
            return
        session = Session()
        # check if the author is in a session
        session.get_session(target=ctx.author.id, database=database)
        if session is None:
            return
        # check if that session is not in this channel
        if session.channel_id != ctx.channel_id:
            return
        # check if the session is accepted
        if session.accepted is False:
            return
        if session is None:
            return
        # check if the session is expired
        if session.check_if_expired():
            # refresh the expiration date
            session.refresh_expiration_date(database=database)
        await ctx.delete()
        # get the original message
        original_message = ctx.content
        # delete the original message
        # get the other user's preferred language
        other_user = session.get_other_user(ctx.author.id)
        # translate the message
        translated_message = GoogleTranslator(
            source="auto", target=other_user.preferred_lang
        ).translate(original_message)
        # get the webhook of the author
        channel: interactions.Channel = await ctx.get_channel()
        webhooks: interactions.Webhook = await channel.get_webhooks()
        # NOTE: I Think this can be done more efficiently. ¯\_(ツ)_/¯
        for webhook in webhooks:
            if webhook.name == ctx.author.username:
                # that is the webhook of the author
                right_webhook = webhook
        # send the translated message to the channel using the webhook
        await right_webhook.execute(
            content=translated_message, avatar_url=ctx.author.avatar_url
        )


def setup(client):
    """Setup function for CopyCat cog"""
    SessionManager(client)
