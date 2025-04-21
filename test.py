import json
with open("config.json", 'r') as f:
    test = json.load(f)
print(test)