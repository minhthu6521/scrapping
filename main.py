import json

from scrapper import get_list_of_apartment_with_details

if __name__ == '__main__':
    data = get_list_of_apartment_with_details()
    write = open('db.json', 'w+')
    write.write(json.dumps(data, ensure_ascii=False))
