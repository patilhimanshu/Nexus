import json

data = {"name": "Umesh", "city": "Pune"}

with open("test.json", "w") as f:
    json.dump(data, f)

print("Saved!")


with open("test.json", "r") as f:
    loaded = json.load(f)

print(loaded["name"])
print(loaded["city"])