"""CopyCat cog"""

import os
import interactions
import asyncio
import pymongo
from deep_translator import GoogleTranslator
from models.session import Session  # pylint: disable=import-error

# from datetime import datetime, timedelta
from models.user import User  # pylint: disable=E0401


pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))

database = pymongo_client.server


class SessionCommands(interactions.Extension):
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
        test = target_user.search_db()

        if test is None:
            # The other user has not finished setting up their account in the bot.
            await ctx.send(
                "The other user has not finished setting up their account in the bot. Please ask them to run `/settings preferred_lang` and follow the instructions.",
                ephemeral=True,
            )
            return
        # register the webhook
        # check if the user is either the initiator or the receiver of a session AND if the session is in the channel
        session_as_doc = database.sessions.find_one(
            {
                "$or": [
                    {"initiator.user_id": int(ctx.author.id)},
                    {"receiver.user_id": int(ctx.author.id)},
                ],
                "channel_id": int(ctx.channel_id),
            }
        )
        if session_as_doc:
            # if so, check if it expired or not
            session = Session()
            if session.check_if_expired(session_as_doc):
                database.sessions.delete_one({"initiator.user_id": int(ctx.author.id)})
                # an expired session was found, so the webhook was deleted and the document was deleted
            elif session.check_if_expired(session_as_doc) is False:
                await ctx.send(
                    ephemeral=True,
                    content="You already have an active session in this channel. Please end it before starting a new one.",
                )
                return

        await author_user.register_webhook(self.client, ctx.channel)

        # register the database
        # user.register_db()  # DEPRECATED
        # send a message to the user
        await ctx.send(
            f"Session started for {author_user.name}!"
        )  # TODO: convert this into a cool embed :)
        # create session object
        session = Session(author_user, target_user, ctx.guild_id, ctx.channel_id)
        object_id = session.register_session(database=database)
        session.oid = object_id
        # ping the specified user that the author_user has requested to start a session with them. ask the user to type /accept_session
        # TODO: Make this a button
        inv = GoogleTranslator(
            source="en", target=f"{target_user.preferred_lang}"
        ).translate(
            "has requested to start a translation with you! Please click the green button to accept! If the user does not accept within 5 minutes, the session will terminate."
        )
        msg = await ctx.send(f"{user.mention}, {author_user.name} {inv}")

        await asyncio.sleep(300)
        # check if the session is still not accepted by finding with the object id
        session.dict_to_session(database.sessions.find_one({"_id": session.oid}))
        if session.accepted is False:
            # if not, delete the session and send a message to the author_user
            database.sessions.delete_one({"_id": session.oid})
            inv = GoogleTranslator(
                source="en", target=f"{target_user.preferred_lang}"
            ).translate("Your session request has expired.")
            await msg.edit(f"{user.mention}, {inv}")

    # @session.subcommand()
    # async def decline(self, ctx):
    #     # TODO: If there are multiple sessions, respond with the Session Manager in decline mode.
    #     """Decline a session"""
    #     try:
    #         session = Session()
    #         session.get_session(database=database, target=ctx.author.id)
    #     except TypeError:
    #         await ctx.send(
    #             "You do not have a session to decline! You can start on with /session start"
    #         )
    #         return
    #     if session is None:
    #         await ctx.send(
    #             "You do not have a session to decline! You can start on with /session start"
    #         )
    #         return
    #     # check if the user sending the command is the same user that initialized the session
    #     if session.initiator.user_id == ctx.author.id:
    #         await ctx.send(
    #             "You are about to decline a session *you* started. Please do this by running the active session manager command.",
    #             ephemeral=True,
    #         )
    #         return
    #     # delete the session from the database

    #     await session.delete(self.client)

    #     await ctx.send("Session declined!", ephemeral=True)

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
        session.get_session(
            target=ctx.author, database=database, channel_id=ctx.channel_id
        )
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
        other_user = session.opposite_user(ctx.author.id)
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
    SessionCommands(client)
