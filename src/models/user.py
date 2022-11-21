"""Model Class for User"""

import os
import interactions
import pymongo

# import database variable from main module

# connect to the pymongo database using the environment variables
pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))
# get the database
database = pymongo_client.server


class PsuedoUser:
    """Class to store a PsuedoUser"""

    def __init__(self, name, user_id) -> None:
        self.name = name
        self.user_id = user_id
        # modifiables
        self.avatar_url = ""
        # self.channel_id = channel_id # REMOVED because I want to make this a check instead of a hard set value (AFTER EACH SESSION IS ENDED, DELETE WEBHOOKS)
        self.webhook_id: int = 0

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
        """Convert the PsuedoUser to a dictionary."""
        return {
            "name": self.name,
            "user_id": int(self.user_id),
            "avatar_url": self.avatar_url,
            "webhook_id": int(self.webhook_id),
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

    def register_db(self):
        """{DEPRECATED} Register the PseudoUser by adding it to the database."""
        # take the attributes of the PsuedoUser and add it to the database
        user = {
            "name": self.name,
            "user_id": self.user_id,
            "avatar_url": self.avatar_url,
            "webhook_id": self.webhook_id,
        }
        users = database.users
        users.insert_one(user)
