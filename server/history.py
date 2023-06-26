import json


class History:
    def __init__(self, items, values, start_date, end_date):
        self.items = items
        self.values = values
        self.start_date = start_date
        self.end_date = end_date

    def to_json(self):
        return json.dumps(self.__dict__)
