import datetime
import json

from scrapper import OikotieScraper
from scrapper import get_list_of_apartment_with_details


if __name__ == '__main__':
    file = open('db.json')
    data = json.load(file)
    for a in data:
        a["time_created"] = datetime.datetime(2020, 9, 10).isoformat()
    print(data)
    write = open('db.json', 'w+')
    write.write(json.dumps(data))
    #get_list_of_apartment_with_details()
