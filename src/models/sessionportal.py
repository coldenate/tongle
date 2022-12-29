"""A file containing a model of a mini discord applet (that uses a paginated embed with buttons and controls) that allows the user to manage their translations sessions"""

import os
import interactions
import asyncio
import pymongo
from deep_translator import GoogleTranslator
from models.session import Session  # pylint: disable=import-error

# from datetime import datetime, timedelta
from models.user import User  # pylint: disable=E0401

LIMIT = 25

pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))

database = pymongo_client.server


class SessionPortal:
    """A model of a mini discord applet (that uses a paginated embed with buttons and controls) that allows the user to manage their translations sessions"""

    def __init__(self, user):
        self.user: interactions.User = user

    modes = {
        "main": "Main Menu",
        "accept": "Accept Sessions",
        "decline": "Decline Sessions",
        "manage": "Manage Sessions",
        "settings": "Settings",
    }

    @classmethod
    def parse_session_portal_custom_id(cls, message, skip: bool = False):
        """
        Extract the custom_id from the message
        The message will have a list of components.
        The last component will be the component holding the data. It is required that this component is present
        Get the last component's components[0].custom_id

        Parse the custom_id of a button in the session portal
        example is lastpage:{last_page},page:{page},mode:{mode}
        return a dictionary of the parsed data that looks like this:
        {
            'lastpage': 0,
            'page': 0,
            'mode': 'main'
        }
        """
        if not skip:

            message_components = message.components
            last_component = message_components[-1]
            custom_id = last_component.components[0].custom_id
        if skip:
            custom_id = message

        parsed = {}
        for item in custom_id.split(","):
            item = item.split(":")
            if item[0] == "mode":
                parsed[item[0]] = item[1]
                continue
            parsed[item[0]] = int(item[1])
        return parsed

    def mode_name_get(self, mode):

        return self.modes[mode]

    async def send_embed(
        self,
        ctx: interactions.ComponentContext,
        client,
        spawn_author: interactions.User,
        mode,
        page,
        hidden=False,
        initial=False,
        loading=True,
    ):
        """Generate the embed for the session portal. Mode can be 'main', 'accept', 'decline', or 'manage'"""

        footer = interactions.EmbedFooter(text=f"Mode: {mode}")
        author = interactions.EmbedAuthor(
            name=f"{int(spawn_author.id)}",
            icon_url=spawn_author.avatar_url,
        )

        # if the index is a negative number, set it to 0
        if page < 0:
            page = 0

        embed = interactions.Embed(
            # type="rich",
            title=f"Sessions Manager - {self.mode_name_get(mode)}",
            description=f"",
            color=0x00FFFF,
            fields=None,
            footer=footer,
            author=author,
        )
        if loading:
            safety_check = await self.loading(
                ctx, embed, ephemeral=hidden, initial=initial
            )
            if safety_check is False:
                return
        embed.thumbnail = None
        accept_emoji = interactions.Emoji(name="✅")
        decline_emoji = interactions.Emoji(name="❌")
        settings_emoji = interactions.Emoji(name="⚙")

        accept_mode_button = interactions.Button(
            style=interactions.ButtonStyle.SUCCESS,
            label="Accept Sessions",
            custom_id="accept_mode",
            disabled=False,
            emoji=accept_emoji,
        )
        decline_mode_button = interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            label="Decline Sessions",
            custom_id="decline_mode",
            disabled=False,
            emoji=decline_emoji,
        )
        manage_mode_button = interactions.Button(
            style=interactions.ButtonStyle.SECONDARY,
            label="Manage Active Sessions",
            custom_id="manage_mode",
            disabled=False,
        )
        settings_mode_button = interactions.Button(
            style=interactions.ButtonStyle.SECONDARY,
            label="Settings",
            custom_id="settings_mode",
            disabled=False,
            emoji=settings_emoji,
        )
        # close button
        close_button = interactions.Button(
            style=interactions.ButtonStyle.DANGER,
            label="Close",
            custom_id="close_sessions_manager",
            disabled=False,
        )
        # generate page control buttons for far_left, left, right, far_right

        components = []
        session_select = await self.generate_select_embed(
            mode,
            page=page,
            embed=embed,
            components=components,
            spawn_author=spawn_author,
        )  # index is 0 because this is a command trigger. on a button press, the index will be calculated.
        if session_select is not None:
            if session_select.options == []:
                session_select = None
        components.append(
            interactions.ActionRow(components=[accept_mode_button, decline_mode_button])
        )
        components.append(
            interactions.ActionRow(
                components=[manage_mode_button, settings_mode_button, close_button]
            )
        )
        if session_select is not None:
            row3 = interactions.ActionRow(components=[session_select])
            components.append(row3)

        # await self.populate_fields(embed, ctx, mode, page, client=client)

        await ctx.edit(embeds=[embed], components=components)

    def get_sessions_for_mode(self, mode, spawn_author: interactions.User):
        if mode == "main":
            return None

        if mode == "settings":
            return None

        if mode == "accept":
            sessions = database.sessions.find(
                {
                    "receiver.user_id": int(spawn_author.id),
                    "accepted": False,
                }
            )

        if mode == "manage" or mode == "decline":
            sessions = database.sessions.find(
                {
                    "$or": [
                        {"receiver.user_id": int(spawn_author.id)},
                        {"initiator.user_id": int(spawn_author.id)},
                    ]
                }
            )
        # for ses in sessions:
        #     print(ses)
        sessions_new = []
        for session in sessions:
            sessions_new.append(Session(dict_convert=session))
        sessions = sessions_new
        return sessions

    async def generate_select_embed(
        self,
        mode,
        # client,
        spawn_author: interactions.User,
        embed: interactions.Embed,
        components: list[interactions.Component],
        page=0,
    ):
        """ "Generate the select menu for the given mode
        Mode can be 'main', 'accept', 'decline', or 'manage'
        'main' will return None
        'accept' will return a select menu with all the sessions that the user can accept (sessions that the user is a receiver for and not accepted)
        'decline' will return a select menu with all the sessions that the user can decline (sessions that the user is a receiver for and not accepted)
        'manage' will return a select menu with all the sessions that the user can manage (sessions that the user is a initiator or receiver for)
        """

        far_left_emoji = interactions.Emoji(name="⏪")
        left_emoji = interactions.Emoji(name="◀")
        right_emoji = interactions.Emoji(name="▶")
        far_right_emoji = interactions.Emoji(name="⏩")

        far_left_button = interactions.Button(
            style=interactions.ButtonStyle.SECONDARY,
            custom_id="far_left_session_select",
            disabled=False,
            emoji=far_left_emoji,
        )
        left_button = interactions.Button(
            style=interactions.ButtonStyle.SECONDARY,
            custom_id="left_session_select",
            disabled=False,
            emoji=left_emoji,
        )
        right_button = interactions.Button(
            style=interactions.ButtonStyle.SECONDARY,
            custom_id="right_session_select",
            disabled=False,
            emoji=right_emoji,
        )
        far_right_button = interactions.Button(
            style=interactions.ButtonStyle.SECONDARY,
            custom_id="far_right_session_select",
            disabled=False,
            emoji=far_right_emoji,
        )

        sessions = self.get_sessions_for_mode(mode=mode, spawn_author=spawn_author)

        # note that there is a maximum of 25 options in a select menu. so we will need to paginate the sessions. index will be the index of the first session to be displayed.

        # this will generate options for the select menu

        if sessions is None:
            if mode == "main":
                return

            # there are no sessions
            elif mode != "settings":
                embed.add_field("There are no sessions to show!", r"¯\_(ツ)_/¯")
                return
            if mode == "settings":

                # we will display the user's bot attributes in the embed fields

                user = User(discord_user=spawn_author)

                embed.add_field(
                    name="Preferred Language",
                    value=f"`{user.preferred_lang}`",
                    inline=True,
                )

                # amount of active sessions

                active_sessions = database.sessions.find(
                    {
                        "$or": [
                            {"receiver.user_id": int(spawn_author.id)},
                            {"initiator.user_id": int(spawn_author.id)},
                        ],
                        "accepted": True,
                    }
                )

                embed.add_field(
                    name="Active Sessions",
                    value=f"`{len(list(active_sessions))}`",
                    inline=True,
                )

                components.append(
                    interactions.ActionRow.new(
                        User.return_language_picker_select_menu()[0]
                    )
                )
                components.append(
                    interactions.ActionRow.new(
                        interactions.Button(
                            label="Can't find your language?",
                            style=interactions.ButtonStyle.PRIMARY,
                            custom_id="preferred_language_modal_spawn",
                        )
                    ),
                )
                return

        # we will paginate the sessions. page will be the index of the first session to be displayed.
        # we will display 25 sessions per page
        # status will be the status of the session (accepted, pending)
        # we will display the sessions in the following format:
        # field name: {session.opposite_user(int(ctx.author.id)).name} ({status})
        # field value: translating into {session.opposite_user(int(ctx.author.id)).preferred_language}

        options = []
        for i, session in enumerate(sessions[page * LIMIT : page * LIMIT + LIMIT]):

            i_human_value = i + page * LIMIT

            # try:
            #     channel = await interactions.get(
            #         client, interactions.Channel, object_id=session.channel_id
            #     )
            # except interactions.LibraryException:
            #     channel_name = "Unknown"
            # if channel is not None:
            #     channel_name = channel.name

            opposite_user = session.opposite_user(int(spawn_author.id))
            status = "Accepted" if session.accepted else "Pending"
            embed.add_field(
                name=f"`{i_human_value+1}.` {opposite_user.name} ({status})",
                value=f"Translating into {opposite_user.preferred_lang} in {session.channel_name}",
                inline=True,
            )
            # get the session object
            # get the initiator and receiver

            # get the status
            # generate the option
            # get channel name with channel id

            opposite_user = session.opposite_user(int(spawn_author.id))
            option = interactions.SelectOption(
                label=f"{i_human_value+1}. {opposite_user.name}",
                description=f"translating into {opposite_user.preferred_lang} in {session.channel_name}",
                value=f"{session.oid}",
            )

            options.append(option)

        # if the session count was above LIMIT, we will need to add the buttons in an action row, and add that to the message - making sure it is the first action row in the messages's component list\
        buttons = []
        if len(sessions) > LIMIT:
            # we will need to add the buttons
            # determine which buttons to omit, example: if we are on the first page, we will set the left buttons to disabled

            if page == 0:
                far_left_button.disabled = True
                left_button.disabled = True

            if page == len(sessions) // LIMIT:
                far_right_button.disabled = True
                right_button.disabled = True

            buttons = [far_left_button, left_button, right_button, far_right_button]

            # if page == 0:
            #     # we are on the first page
            #     buttons = [right_button, far_right_button]
            # elif page == len(sessions) // LIMIT:
            #     # we are on the last page
            #     buttons = [left_button, far_left_button]
            # else:
            #     # we are on a page in the middle
            #     buttons = [
            #         left_button,
            #         far_left_button,
            #         right_button,
            #         far_right_button,
            #     ]
            action_row = interactions.ActionRow(components=buttons)

            components.insert(0, action_row)

        # compute the last index of the list
        last_page = len(sessions) // LIMIT

        embed.footer.text = embed.footer.text + (f" | Page {page+ 1} of {last_page+1}")

        select = interactions.SelectMenu(
            custom_id=f"""lastpage:{last_page},page:{page},mode:{mode}""",
            placeholder=f"Select a session to {mode}",
            options=options,
        )

        return select

    async def loading(
        self,
        ctx: interactions.ComponentContext | interactions.CommandContext,
        embed: interactions.Embed = None,
        ephemeral: bool = False,
        initial: bool = False,
    ):
        """Loading Screen"""
        if isinstance(ctx, interactions.CommandContext):
            await ctx.defer(ephemeral=ephemeral)
        elif isinstance(ctx, interactions.ComponentContext):
            message_embeds = ctx.message.embeds
            if message_embeds is not None or not []:
                if int(ctx.author.id) != int(message_embeds[0].author.name):
                    await ctx.send(
                        "You do not have permission to do this!", ephemeral=True
                    )
                    return False
            await ctx.defer(edit_origin=True)

        # edit the embed to have a thumbnail of a loading gif
        if embed is not None:
            current_embed = embed
            current_embed.set_thumbnail(
                url="https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"
            )
        if initial:
            await ctx.send(embeds=[current_embed])
            return
        # await ctx.edit(embeds=[current_embed])
