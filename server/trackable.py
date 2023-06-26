from enum import Enum
import json
import datetime

date_format = '%Y-%m-%d'


class TrackableType(Enum):
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SCORE = 'score'


class Trackable:
    def __init__(self, id, owner, created, name, type):
        self.id = id
        self.owner = owner
        self.created = datetime.datetime.strftime(created, date_format)
        self.name = name
        self.type = TrackableType(type).value

    def to_json(self):
        return json.dumps(self.__dict__)

    def validate_value(self, value):
        try:
            if self.type == 'number':
                num = int(value)
                if isinstance(num, int):
                    return True
            elif self.type == 'score':
                val = float(value)
                if isinstance(val, float) and val <= 10:
                    return True
            elif self.type == 'boolean':
                is_bool = isinstance(value, bool)
                if is_bool:
                    return True
        except ValueError:
            return False
        return True


@staticmethod
def create_trackable_from_row(row):
    return Trackable(row['id'], row['owner_id'],
                     row['created'], row['name'], row['type'])
