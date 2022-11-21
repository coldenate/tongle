"""The pythonic class of the Translation Session"""

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

    def convert_to_dict(self) -> dict:
        """convert self to a dictiionary"""
        return {
            "initiator": self.initiator.convert_to_dict(),
            "receiver": self.receiver.convert_to_dict(),
            "guild_id": int(self.guild_id),
            "channel_id": int(self.channel_id),
            "accepted": self.accepted,
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
