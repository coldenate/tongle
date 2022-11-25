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
        preferred_lang=None,
        discord_user: interactions.User = None,  # type: ignore
    ) -> None:
        """Initialize the User."""
        if discord_user:

            user_id = int(discord_user.id)
            name = discord_user.username
            discriminator = discord_user.discriminator
        self.name: str | None = name
        self.user_id: int | None | str = int(user_id)  # type: ignore
        # modifiables
        self.discriminator: str | None = discriminator
        # self.channel_id = channel_id # REMOVED because I want to make this a check instead o
        # f a hard set value (AFTER EACH SESSION IS ENDED, DELETE WEBHOOKS)
        self.preferred_lang: str | None = preferred_lang
        self.webhook_id = 0

    # constructor method that takes in a dictionary and returns a PsuedoUser object
    # @classmethod
    # def from_dict(cls, data: dict):
    #     """Create a PsuedoUser from a dictionary."""
    #     return cls(data["name"], data["user_id"])

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
        }

    async def register_webhook(self, client, ctx):
        """Register the PseudoUser by creating a webhook with interactions."""

        user = await interactions.Webhook.create(
            client=client._http,  # pylint: disable=protected-access
            channel_id=ctx.channel_id,
            name=self.name,
        )
        user.id = self.webhook_id  # type: ignore
        user.avatar = ctx.author.get_avatar_url()

    def register_db(self) -> None:
        """Register the User by adding it to the database."""
        # take the attributes of the PsuedoUser and add it to the database
        # {
        #   "user_id": 123456789,
        #   "username": "username",
        #   "discriminator": "1234",
        #   "preferred_lang": "en",

        user = self.convert_to_dict()

        users = database.users
        users.insert_one(user)

    def search_db(self):
        """Search the database for the given user_id. returns the first document match"""
        users = database.users
        user = users.find_one({"user_id": int(self.user_id)})
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
        self.name = doc["username"]
        self.discriminator = doc["discriminator"]
        self.preferred_lang = doc["preferred_lang"]

    def update_db(self) -> None:
        """first, search the database for the user. Replace the first document found with the n
        ew user."""
        users = database.users
        new_doc = self.convert_to_dict()
        users.replace_one({"user_id": self.user_id}, new_doc)
        # find the user in the database
        doc = self.search_db()  # this is safe because we are searching
        # for the user_id, which is unique and won't change.
        self.populate_from_mongodb(doc)

    # convert a dictionary to a PsuedoUser object
    @classmethod
    def dict_to_psuedo_user(cls, psuedo_user_dict):
        """Convert a dictionary to a PsuedoUser object"""
        return User(
            user_id=psuedo_user_dict["user_id"], name=psuedo_user_dict["username"]
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
