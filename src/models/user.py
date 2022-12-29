"""Model Class for User"""

import os
import interactions
import pymongo

# import database variable from main module

# connect to the pymongo database using the environment variables
pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))
# get the database
database = pymongo_client.server


class User:
    """Class to store a PsuedoUser"""

    def __init__(
        self,
        name=None,
        user_id=None,
        discriminator=None,
        preferred_lang="en",
        avatar_url=None,
        discord_user: interactions.User = None,  # type: ignore
    ) -> None:
        """Initialize the User."""
        if discord_user:

            user_id = int(discord_user.id)
            name = discord_user.username
            discriminator = discord_user.discriminator
            avatar_url = discord_user.avatar_url
        self.name: str | None = name
        self.user_id: int | None | str = int(user_id)  # type: ignore
        # modifiables
        self.discriminator: str | None = discriminator
        # self.channel_id = channel_id # REMOVED because I want to make this a check instead o
        # f a hard set value (AFTER EACH SESSION IS ENDED, DELETE WEBHOOKS)
        self.avatar_url: str | None = avatar_url
        self.preferred_lang: str | None = preferred_lang
        self.webhook_id = 0

    # constructor method that takes in a dictionary and returns a PsuedoUser object
    # @classmethod
    # def from_dict(cls, data: dict):
    #     """Create a PsuedoUser from a dictionary."""
    #     return cls(data["name"], data["user_id"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    # function that converts class to a dict
    def convert_to_dict(self) -> dict:
        """Convert the User to a dictionary."""
        return {
            "user_id": int(self.user_id),
            "username": self.name,
            "discriminator": self.discriminator,
            "preferred_lang": self.preferred_lang,
            "avatar_url": self.avatar_url,
        }

    async def get_webhook(
        self,
        client: interactions.Client,
        channel: interactions.Channel,
        creation_fallback: bool = True,
    ):
        """Get the webhook for the user."""
        # Search the given channel for a webhook with the user's name. If it exists, return it. If not, create it.

        webhooks = await channel.get_webhooks()

        for webhook in webhooks:
            if webhook.name == self.name:
                return webhook

        # if the webhook doesn't exist, create it.
        if creation_fallback:
            return self.register_webhook(client, channel)

    async def register_webhook(self, client, channel: interactions.Channel):
        """Register the PseudoUser by creating a webhook with interactions."""
        # FIXME: Would here be a good timet o check for duplicates?
        user = await interactions.Webhook.create(
            client=client._http,  # pylint: disable=protected-access
            channel_id=channel.id,
            name=self.name,
        )
        user.id = self.webhook_id  # type: ignore
        return user

    def register_db(self) -> None:
        """Register the User by adding it to the database."""

        user = self.convert_to_dict()

        users = database.users
        users.insert_one(user)

    def search_db(self):
        """Search the database for the given user_id. converts the document back into self"""
        users = database.users
        user = users.find_one({"user_id": int(self.user_id)})
        if user is not None:
            self.populate_from_mongodb(user)
        return user

    @classmethod
    def return_language_picker_modal(cls):
        """return the language picker to the command ephermally."""
        components = [
            interactions.TextInput(
                label="Or type the 639-1 Language Code Here.",
                custom_id="lang_input",
                required=False,
                style=interactions.TextStyleType.SHORT,
            ),
        ]
        modal = interactions.Modal(
            title="Select your preferred language",
            # description="""Please select your preferred language from the dropdown
            #  menu below. If it cannot be found. enter the 639-1 Language Code. "
            # What is that?" <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>""",
            components=components,
            custom_id="lang_modal",
        )
        return modal
        #  send a message saying "if your language is not listed, enter in the 639-1 code for your
        #  language. https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes"

    def populate_from_mongodb(self, doc) -> None:
        """Populate the User from a MongoDB document."""
        self.user_id = doc["user_id"]
        # an error can occur here where
        self.name = doc["username"]
        self.discriminator = doc["discriminator"]
        self.preferred_lang = doc["preferred_lang"]

    def update_db(self) -> None:
        """first, search the database for the user. Replace the first document found with the n
        ew user."""
        users = database.users
        new_doc = self.convert_to_dict()

        # check if the user hasn't changed

        old_doc = users.find_one({"user_id": int(self.user_id)})

        if old_doc is None:
            self.register_db()
            return
        if old_doc == new_doc:
            return

        users.replace_one({"user_id": self.user_id}, new_doc)
        # find the user in the database
        doc = self.search_db()  # this is safe because we are searching
        # for the user_id, which is unique and won't change.
        self.populate_from_mongodb(doc)

    # convert a dictionary to a PsuedoUser object
    # TODO: add a auto construxtion in the __init__ method
    @classmethod
    def dict_to_user(cls, user_dict):
        """Convert a dictionary to a PsuedoUser object"""
        return User(
            user_id=user_dict["user_id"],
            name=user_dict["username"],
            discriminator=user_dict["discriminator"],
            preferred_lang=user_dict["preferred_lang"],
            avatar_url=user_dict["avatar_url"],
        )

    @classmethod
    def return_language_picker_select_menu(cls) -> list[interactions.SelectMenu]:
        """returnt he language picker slecte menu :D"""
        components = [
            interactions.SelectMenu(
                custom_id="lang_select",
                options=[
                    interactions.SelectOption(label="English", value="en"),
                    interactions.SelectOption(label="Español", value="es"),
                    interactions.SelectOption(label="Français", value="fr"),
                    interactions.SelectOption(label="Deutsch", value="de"),
                    interactions.SelectOption(label="Italiano", value="it"),
                    interactions.SelectOption(label="日本語", value="ja"),
                    interactions.SelectOption(label="한국어", value="ko"),
                    interactions.SelectOption(label="Português", value="pt"),
                    interactions.SelectOption(label="Русский", value="ru"),
                    interactions.SelectOption(label="中文", value="zh"),
                ],
                placeholder="Please select your preferred language from the dropdown menu below.",
            ),
        ]
        return components

    async def delete_webhook(self, client, channel: interactions.Channel) -> None:
        """Delete the user's webhook."""
        try:
            webhook = await self.get_webhook(client, channel, creation_fallback=False)
        except ValueError:
            return False
        await webhook.delete()
