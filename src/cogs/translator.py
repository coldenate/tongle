"""translator.py"""

import asyncio
from dotenv import dotenv_values
import interactions
from deep_translator import GoogleTranslator
from models.user import User
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

    @interactions.extension_message_command(name="translate")
    async def lang_input(self, ctx):
        """Translate a message"""
        await ctx.defer()

        # get user's configurated language
        user = User(discord_user=ctx.author.user)
        user.search_db()  # this will load the preferred language of the user

        # if user doens't have one, prompt them to do so.
        if user.preferred_lang is None:  # type: ignore
            m = await ctx.channel.send(
                f"Hey <@{ctx.author.user.id}>, you have not registered a preferred language!\n***Simply run `/settings preferred_language`***",
            )
            # delete this message after 20 seconds
            await asyncio.sleep(20)
            await m.delete()
            return

        # translate the message into their configured language

        translated = GoogleTranslator(
            source="auto", target=f"{user.preferred_lang}"
        ).translate(ctx.target.content)

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
        await ctx.send(embeds=[embed], ephemeral=True)


def setup(client):
    """Setup function for translator.py"""
    Translator(client)
