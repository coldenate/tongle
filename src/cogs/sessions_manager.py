"""Sessions Management Cog"""

import os
import interactions
import pymongo
from deep_translator import GoogleTranslator
import asyncio
from bson import ObjectId
from models.session import Session  # pylint: disable=import-error
from models.sessionportal import SessionPortal  # pylint: disable=import-error

# from datetime import datetime, timedelta
from models.user import User  # pylint: disable=E0401


pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))

database = pymongo_client.server


class SessionsManager(interactions.Extension):
    """A cog to manage a user's sessions"""

    def __init__(self, client):
        self.client: interactions.Client = client

        # command with options for mode that include accept, decline, manage, and settings

    @interactions.extension_command(
        name="sessions",
        description="Manage your translation sessions",
    )
    @interactions.option(
        choices=[
            interactions.Choice(name="Accept Sessions", value="accept"),
            interactions.Choice(name="Decline Sessions", value="decline"),
            interactions.Choice(name="Manage Sessions", value="manage"),
            interactions.Choice(name="Settings", value="settings"),
        ],
        name="mode",
        description="The mode to use",
        required=False,
    )
    async def run(
        self,
        ctx: interactions.ComponentContext,
        mode: str = None,
    ):
        """Run the session manager"""
        hidden = False  # False until the api is updated
        if mode is None:
            mode = "main"

        await SessionPortal(ctx.author).send_embed(
            ctx=ctx,
            mode=mode,
            page=0,
            client=self.client,
            hidden=hidden,
            initial=True,
            spawn_author=ctx.author,
        )

    # handling pagination buttons found in sessionportal.py
    @interactions.extension_component("far_left_session_select")
    async def far_left_session_select(self, ctx: interactions.ComponentContext):

        parsed = SessionPortal.parse_session_portal_custom_id(ctx.message)
        mode = parsed["mode"]

        page = 0  # because it is far left it will always be 0
        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode=f"{mode}",
            page=page,
            client=self.client,
            initial=False,
        )

    @interactions.extension_component("left_session_select")
    async def left_session_select(self, ctx: interactions.ComponentContext):
        parsed = SessionPortal.parse_session_portal_custom_id(ctx.message)
        mode = parsed["mode"]
        page = parsed["page"]

        page -= 1

        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode=f"{mode}",
            page=page,
            client=self.client,
            initial=False,
        )

    @interactions.extension_component("right_session_select")
    async def right_session_select(self, ctx: interactions.ComponentContext):
        parsed = SessionPortal.parse_session_portal_custom_id(ctx.message)
        mode = parsed["mode"]
        page = parsed["page"]

        page += 1
        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode=f"{mode}",
            page=page,
            client=self.client,
            initial=False,
        )

    @interactions.extension_component("far_right_session_select")
    async def far_right_session_select(self, ctx: interactions.ComponentContext):
        parsed = SessionPortal.parse_session_portal_custom_id(ctx.message)
        mode = parsed["mode"]
        page = parsed["lastpage"]

        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode=f"{mode}",
            page=page,
            client=self.client,
            initial=False,
        )

    # handling mode buttons found in sessionportal.py
    @interactions.extension_component("accept_mode")
    async def accept_mode(self, ctx: interactions.ComponentContext):
        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode="accept",
            page=0,
            client=self.client,
            initial=False,
        )

    @interactions.extension_component("decline_mode")
    async def decline_mode(self, ctx: interactions.ComponentContext):
        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode="decline",
            page=0,
            client=self.client,
            initial=False,
        )

    @interactions.extension_component("manage_mode")
    async def manage_mode(self, ctx: interactions.ComponentContext):
        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode="manage",
            page=0,
            client=self.client,
            initial=False,
        )

    @interactions.extension_component("settings_mode")
    async def settings_mode(self, ctx: interactions.ComponentContext):
        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx,
            mode="settings",
            page=0,
            client=self.client,
            initial=False,
        )

    @interactions.extension_component("close_sessions_manager")
    async def close_sessions_manager(self, ctx: interactions.ComponentContext):

        safety_check = await SessionPortal(ctx.author).loading(ctx=ctx)
        if safety_check is False:
            return
        await ctx.message.delete()

    # handling a selection of a session found in sessionportal.py
    @interactions.extension_listener()
    async def on_component(self, ctx: interactions.ComponentContext):

        if ctx.type != interactions.ComponentType.SELECT:
            return

        if not ctx.custom_id.startswith("lastpage"):
            return
        await ctx.defer(edit_origin=True)

        parsed = SessionPortal.parse_session_portal_custom_id(ctx.custom_id, skip=True)

        page = parsed["page"]

        mode = parsed["mode"]

        options = ctx.data.values

        if mode == "accept":
            for option in options:
                session_dict = database.sessions.find_one({"_id": ObjectId(oid=option)})

                if session_dict is None:
                    return
                session = Session(dict_convert=session_dict)
                session.accepted = True
                session.push_session(self, database)

        if mode == "decline":
            for option in options:
                session_dict = database.sessions.delete_one(
                    {"_id": ObjectId(oid=option)}
                )

                if session_dict is None:
                    return

        if mode == "manage":
            for option in options:
                session_dict = database.sessions.find_one({"_id": ObjectId(oid=option)})

                if session_dict is None:
                    return
                session = Session(dict_convert=session_dict)
                session.paused = not session.paused
                session.push_session(self, database)

        await asyncio.sleep(0.5)

        await SessionPortal(ctx.author).send_embed(
            spawn_author=ctx.author,
            ctx=ctx.message,
            mode=f"{mode}",
            page=page,
            client=self.client,
            initial=False,
            loading=False,
        )

    async def safety_check(
        self,
        message_embeds: list[interactions.Embed] | None,
        author: interactions.User,
        ctx: interactions.ComponentContext,
    ):
        if message_embeds is not None or not []:
            if author.id != int(message_embeds[0].author.name):
                msg = await ctx.send("That is not your embed!", ephemeral=True)
                return False


def setup(client):
    """Setup function for CopyCat cog"""
    SessionsManager(client)
