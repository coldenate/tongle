"""conversion functions"""

# convert a dictionary to a Session object
from models.session import Session  # pylint: disable=import-error
from models.user import User  # pylint: disable=import-error


def dict_to_session(session_dict):
    """Convert a dictionary to a Session object"""
    return Session(
        dict_to_psuedo_user(session_dict["initiator"]),
        dict_to_psuedo_user(session_dict["receiver"]),
        session_dict["guild_id"],
        session_dict["channel_id"],
    )


# convert a dictionary to a PsuedoUser object
def dict_to_psuedo_user(psuedo_user_dict):
    """Convert a dictionary to a PsuedoUser object"""
    return User(user_id=psuedo_user_dict["user_id"], name=psuedo_user_dict["name"])
