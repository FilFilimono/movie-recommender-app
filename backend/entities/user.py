
class User:
    def __init__(self, id, username, hash_password):
        self.id = id
        self.username = username
        self._hash_password = hash_password
    
        
    