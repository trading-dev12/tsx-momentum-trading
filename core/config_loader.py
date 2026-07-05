import json


def load_settings():
    with open("config/settings.json", "r") as file:
        settings = json.load(file)

    return settings