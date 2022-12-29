"""The pythonic class of the Translation Session"""

from datetime import timedelta
import datetime
import interactions
from datetime import datetime

from models.user import User  # pylint: disable=import-error
import pymongo
import os
from bson.objectid import ObjectId

pymongo_client = pymongo.MongoClient(os.environ.get("ATLAS_URI"))

database = pymongo_client.server


class Session:
    """Class desribing the attributes of a translation session"""

    def __init__(
        self,
        initiator: User = None,
        receiver: User = None,
        guild_id: int | interactions.Snowflake = None,
        channel_id: int | interactions.Snowflake = None,
        accepted: bool = False,
        expiration_date: timedelta = timedelta(hours=2),
        channel_name: str | None = None,
        dict_convert=None,
    ) -> None:
        """Initialize the session object"""
        if dict_convert is not None:
            self.dict_to_session(dict_convert)
            return
        self.initiator: User = initiator
        self.receiver: User | None = receiver
        self.guild_id: int | interactions.Snowflake = guild_id
        self.channel_id: int | interactions.Snowflake = channel_id
        self.channel_name: str | None = channel_name
        # if the guild id is a snowflake, convert it to an int
        if isinstance(guild_id, interactions.Snowflake):
            self.guild_id: int = int(guild_id)
        # if the channel id is a snowflake, convert it to an int
        if isinstance(channel_id, interactions.Snowflake):
            self.channel_id: int = int(channel_id)
        self.accepted: bool = accepted
        # an expiration date for the session using timedelta
        self.expiration_date: timedelta = expiration_date

        self.oid: ObjectId = None  # IMPORTANT: this value is only created by MongoDB
        self.paused: bool | None = False

        # attempt to pull from MongoDB

    def refresh_expiration_date(self, target_database):
        """Refresh the expiration date of the session"""
        self.expiration_date = datetime.now() + timedelta(hours=2)
        self.push_session(target_database)

    # consructor method that takes in a dictionary and returns a Session object
    # @classmethod
    # def from_dict(cls, session_dict):
    #     """Create a session object from a dictionary"""
    #     return cls(
    #         PsuedoUser.from_dict(session_dict["initiator"]),
    #         PsuedoUser.from_dict(session_dict["receiver"]),
    #         session_dict["guild_id"],
    #         session_dict["channel_id"],
    #     )

    def check_if_expired(self, mongodoc=None):
        """Check if the session has expired. Retuerns True if expired, False if not"""
        if mongodoc is not None:

            self.dict_to_session(mongodoc)

        present = datetime.now()
        return self.expiration_date < present
        # the session has expired, so delete the webhook, and delete the document in the database.
        # await webhook.delete()
        # database.sessions.delete_one({"initiator.user_id": ctx.author.id})

    def convert_timedelta_to_datetime(self, in_td: timedelta):
        """Convert a timedelta to a datetime"""
        return datetime.now() + in_td

    def convert_to_dict(self) -> dict:
        """convert self to a dictiionary"""
        # if the expiration date is a timedelta, convert it to a datetime
        if isinstance(self.expiration_date, timedelta):
            self.expiration_date = self.convert_timedelta_to_datetime(
                self.expiration_date
            )
        # if the expiration date is a datetime, do nothing
        elif isinstance(self.expiration_date, datetime):
            pass
        return {
            "initiator": self.initiator.convert_to_dict(),
            "receiver": self.receiver.convert_to_dict(),
            "guild_id": int(self.guild_id),
            "channel_id": int(self.channel_id),
            "accepted": self.accepted,
            "expiration_date": self.expiration_date,
            "paused": self.paused,
            "channel_name": self.channel_name,
        }

    def push_session(self, database):
        """pushing the session in the database"""
        sessions = database.sessions

        return sessions.update_one(
            {"_id": self.oid},
            {"$set": self.convert_to_dict()},
        )

    def register_session(self, database):
        """Register the session in the database"""
        sessions = database.sessions
        inserted_id = sessions.insert_one(self.convert_to_dict()).inserted_id
        return inserted_id

    def dict_to_session(self, session_dict):
        """Convert a dictionary to a Session object"""

        # User.dict_to_psuedo_user(session_dict["initiator"]),
        # User.dict_to_psuedo_user(session_dict["receiver"]),
        # session_dict["guild_id"],
        # session_dict["channel_id"],
        # expiration_date=session_dict[
        #     "expiration_date"
        # ],  # will be a datetime object
        # accepted=session_dict["accepted"],

        self.initiator = User.dict_to_user(session_dict["initiator"])
        self.receiver = User.dict_to_user(session_dict["receiver"])
        self.guild_id = session_dict["guild_id"]
        self.channel_id = session_dict["channel_id"]
        self.expiration_date = session_dict[
            "expiration_date"
        ]  # will be a datetime object
        self.accepted = session_dict["accepted"]
        self.oid = session_dict["_id"]
        self.paused = session_dict["paused"]
        self.channel_name = session_dict["channel_name"]

    # def get_session(self, database, oid: ObjectId):
    #     """Get the session from the database. THIS METHOD WILL GET THE SESSION BY SEARCHING FOR MATCHING TARGET IDS VIA INITIATOR AND RECEIVER"""
    #     sessions = database.sessions
    #     session_as_doc = sessions.find_one({"_id": self.oid})
    #     if session_as_doc is None:
    #         return None
    #     self.dict_to_session(session_as_doc)

    def get_session(self, database, channel_id, target):
        """Get a session, by searching the database for a session with a matching channel id and target user id"""

        sessions = database.sessions
        session_as_doc = sessions.find_one(
            {
                "$and": [
                    {"channel_id": int(channel_id)},
                    {
                        "$or": [
                            {"initiator.user_id": int(target.id)},
                            {"receiver.user_id": int(target.id)},
                        ]
                    },
                ]
            }
        )
        if session_as_doc is None:
            return None
        self.dict_to_session(session_as_doc)

    def get_sessions(self, database, target_user: interactions.User):
        """Get all the sessions that a given user is apart of."""
        sessions = database.sessions
        # find all sesisons where the initiator or receiver is the target user
        session_as_docs = sessions.find(
            {
                "$or": [
                    {"initiator.user_id": target_user.id},
                    {"receiver.user_id": target_user.id},
                ]
            }
        )
        if session_as_docs is None:
            return None

        sessions = []
        for session in session_as_docs:
            sessions.append(self.dict_to_session(session))

        return sessions

    def get_sessions_to_accept(self, database, target_user: interactions.User):
        """Get all the sessions that the user is a receiver of, and needs to accept."""
        sessions = database.sessions
        # find all sesisons where the initiator or receiver is the target user
        session_as_docs = sessions.find(
            {
                "$and": [
                    {"receiver.user_id": target_user.id},
                    {"accepted": False},
                ]
            }
        )
        if session_as_docs is None:
            return None

        sessions = []
        for session in session_as_docs:
            sessions.append(self.dict_to_session(session))

        return sessions

    def opposite_user(self, given_id):
        """Return the initiator or receiver that is not the given id"""
        if self.initiator.user_id == given_id:
            return self.receiver
        if self.initiator.user_id != given_id:
            return self.initiator

    async def delete(self, client):
        """Deletes session from database, and deletes the webhooks associated with the initiator and receiever."""
        # delete the webhooks
        channel = await interactions.get(
            client=client, obj=interactions.Channel, object_id=self.channel_id
        )
        await self.initiator.delete_webhook(client, channel)
        await self.receiver.delete_webhook(client, channel)
        # delete the session from the database
        sessions = database.sessions
        sessions.delete_one({"initiator.user_id": self.initiator.user_id})
