# A cog that uses modals to configure a user's settings

import os
import interactions
import pymongo

from models.user import User  # pylint: disable=import-error

pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))
# get the database
database = pymongo_client.server


class Settings(interactions.Extension):
    """Extension class for settings commands"""

    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(
        name="settings",
        description="Configure your settings",
    )
    async def settings(self, ctx: interactions.CommandContext) -> None:
        """Base command for settings"""

    @settings.subcommand(
        name="preferred_language", description="Set your preferred language"
    )
    async def preferred_language(self, ctx):
        """Spawn the preferred language modal"""

        # Send a hidden message that says "Select your preferred language" and include a button component that will popup the modal if the user cannot find their language
        await ctx.send(
            "Select your preferred language",
            components=[
                interactions.ActionRow.new(
                    User.return_language_picker_select_menu()[0]
                ),
                interactions.ActionRow.new(
                    interactions.Button(
                        label="Can't find your language?",
                        style=interactions.ButtonStyle.PRIMARY,
                        custom_id="preferred_language_modal_spawn",
                    )
                ),
            ],
        )

    @interactions.extension_component("preferred_language_modal_spawn")
    async def preferred_language_modal_spawn(self, ctx: interactions.ComponentContext):
        """Spawn the preferred language modal"""

        modal = User.return_language_picker_modal()
        await ctx.popup(modal)

    @interactions.extension_component("lang_select")
    async def lang_select(self, ctx: interactions.ComponentContext, options):
        """Set the user's preferred language"""

        # get the selected option
        selected_option = options[0]
        # get the user
        user = User(discord_user=ctx.author.user, preferred_lang=selected_option)  # type: ignore # type: ignore

        # set the preferred language

        # update the database
        user.update_db()
        # send a message to the user
        await ctx.send(
            f"Your preferred language has been set to {selected_option}!",
            ephemeral=True,
        )

    @interactions.extension_modal("lang_modal")
    async def lang_modal(
        self, ctx: interactions.CommandContext, text_input_response: str
    ):
        """Set the user's preferred language"""

        # get the user
        user = User(discord_user=ctx.author.user, preferred_lang=text_input_response)

        user.update_db()

        await ctx.send(
            f"Your preferred language has been set to {text_input_response}!",
            ephemeral=True,
        )


def setup(client):
    """Setup function for the extension"""
    Settings(client)
