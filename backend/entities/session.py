class Session:
    def __init__(self, token, user_id, created_at=None):
        self.token = token
        self.user_id = user_id
        self.created_at = created_at

    def to_dict(self):
        return {
            "token": self.token,
            "user_id": self.user_id,
            "created_at": self.created_at,
        }
