"""The pythonic class of the Translation Session"""

from datetime import timedelta
import datetime
import interactions

from models.user import PsuedoUser  # pylint: disable=import-error


class Session:
    """Class desribing the attributes of a translation session"""

    def __init__(
        self,
        initiator: PsuedoUser,
        receiver: PsuedoUser,
        guild_id: int | interactions.Snowflake,
        channel_id: int | interactions.Snowflake,
    ) -> None:
        self.initiator: PsuedoUser = initiator
        self.receiver: PsuedoUser = receiver
        self.guild_id: int | interactions.Snowflake = guild_id
        self.channel_id: int | interactions.Snowflake = channel_id
        self.accepted: bool = False
        # an expiration date for the session using timedelta
        self.expiration_date: timedelta = timedelta(days=1)

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

    def convert_timedelta_to_datetime(self, in_td: timedelta) -> datetime.datetime:
        """Convert a timedelta to a datetime"""
        return datetime.datetime.now() + in_td

    def convert_to_dict(self) -> dict:
        """convert self to a dictiionary"""
        return {
            "initiator": self.initiator.convert_to_dict(),
            "receiver": self.receiver.convert_to_dict(),
            "guild_id": int(self.guild_id),
            "channel_id": int(self.channel_id),
            "accepted": self.accepted,
            "expiration_date": self.convert_timedelta_to_datetime(self.expiration_date),
        }

    def sync_session(self, database):
        """Sync the session in the database"""
        sessions = database.sessions

        sessions.update_one(
            {"initiator.user_id": self.initiator.user_id},
            {"$set": self.convert_to_dict()},
        )

    def register_session(self, database):
        """Register the session in the database"""
        sessions = database.sessions
        sessions.insert_one(self.convert_to_dict())
