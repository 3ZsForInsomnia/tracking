import datetime
import json


class User:
    def __init__(self, id, username, name, created):
        self.id = id
        self.username = username
        self.name = name
        self.created = datetime.datetime.fromtimestamp(created)

    def get_name(self):
        if self.name is not None:
            return self.name
        else:
            return self.username

    def to_json(self):
        return json.dumps(self.__dict__)
