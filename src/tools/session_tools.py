"""Tools regarding session management"""


def get_session(target, database):
    """Get the session from the database"""
    sessions = database.sessions
    return sessions.find_one({"receiver.user_id": int(target)})
