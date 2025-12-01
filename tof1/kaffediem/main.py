import csv
import json

data = {}

with open("order-export.csv") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        order_id = row["order_id"]
        order_items = json.loads(row["order_items"])
        print(order_id, order_items)
        data[order_id] = {
            "order_items": [
                {
                    "id": order_items[0]["order_item_id"],
                    "item_name": order_items[0]["item_name"],
                    "customizations": order_items[0]["customizations"],
                }
            ]
        }

print(data)
