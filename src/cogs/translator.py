"""translator.py"""

from dotenv import dotenv_values
import interactions
from deep_translator import GoogleTranslator
from permissions import Permissions  # pylint: disable=import-error


config = dotenv_values(".env")


def generate_selectoption(translator):
    """Generate a list of select options for the language selection"""

    langs_dict = GoogleTranslator.get_supported_languages(
        self=translator, as_dict=True  # type: ignore
    )  # output: {arabic: ar, french: fr, english:en etc...}
    options = []  # list of interactions.SelectOptions
    for lang in langs_dict:
        options.append(interactions.SelectOption(label=lang, value=langs_dict[lang]))

    return options


class Translator(interactions.Extension):
    """Extension class for translation commands"""

    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(
        name="base_command",
        description="This description isn't seen in UI (yet?)",
        options=[
            interactions.Option(
                name="command_name",
                description="A descriptive description",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="option",
                        description="A descriptive description",
                        type=interactions.OptionType.INTEGER,
                        required=False,
                    ),
                ],
            ),
            interactions.Option(
                name="second_command",
                description="A descriptive description",
                type=interactions.OptionType.SUB_COMMAND,
                options=[
                    interactions.Option(
                        name="second_option",
                        description="A descriptive description",
                        type=interactions.OptionType.STRING,
                        required=True,
                    ),
                ],
            ),
        ],
    )
    async def cmd(
        self,
        ctx: interactions.CommandContext,
        sub_command: str,
        second_option: str = "",
        option: int = 0,
    ):
        """Command"""
        if sub_command == "command_name":
            await ctx.send(
                f"You selected the command_name sub command and put in {option}"
            )
        elif sub_command == "second_command":
            await ctx.send(
                f"You selected the second_command sub command and put in {second_option}"
            )

    @interactions.extension_message_command(
        name="translate",
        default_member_permissions=interactions.Permissions(
            Permissions.SEND_MESSAGES.value
        ),
    )
    async def lang_input(self, ctx):
        """Translate a message"""
        translated = GoogleTranslator(source="es", target="en").translate(
            ctx.target.content
        )
        embed = interactions.Embed(
            title="Click to view original message",
            description=translated,
            # add a field that says "Original message" and the original message
            fields=[
                interactions.EmbedField(
                    name="Original message", value=ctx.target.content
                )
            ],
            # make a link that links to the origingla message
            url=f"https://discord.com/channels/{ctx.guild_id}/{ctx.channel_id}/{ctx.target.id}",
            footer=interactions.EmbedFooter(
                text=f"Original message author {ctx.target.author.username}",
                icon_url=ctx.target.author.avatar_url,
            ),
            color=interactions.Color.fuchsia(),
        )
        await ctx.send(embeds=[embed])
        # get user's configurated language

        # if user doens't have one, prompt them to do so.

        # translate the message into their configured language


def setup(client):
    """Setup function for translator.py"""
    Translator(client)
