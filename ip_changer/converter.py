from ast import arg
import json
from sys import argv

from attr import dataclass
import requests


@dataclass
class Proxy:
    country: str
    ping: str
    protocol: str
    anonymityLevel: str
    address: str


def main():
    json_file = "./proxies.json"
    unique = []
    seen = set()
    with open(json_file, "r") as f:
        data = json.load(f)

        txt_data = []

        for row in data:
            row1 = {
                "country": row["country"],
                "ping": row["ping"],
                "protocol": row["protocols"][0],
                "anonymityLevel": row["anonymityLevel"],
                "address": row["address"],
            }
            row = Proxy(**row1)
            frozenset_dict = frozenset(row.__dict__.items())
            if frozenset_dict not in seen:
                unique.append(row)
                seen.add(frozenset_dict)

        for row in unique:
            txt_data.append(f"{row.protocol}://{row.address}")

        with open("proxies.txt", "w") as f:
            f.write("\n".join(txt_data))


def freeProxies():
    response = requests.get(
        "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&country=es&proxy_format=protocolipport&format=json"
    )

    data = response.json()

    txt_data = []
    for row in data["proxies"]:
        protocol = row["protocol"]
        address = row["ip"]
        port = row["port"]

        txt_data.append(f"{protocol}://{address}:{port}")

    with open("proxies.txt", "w") as f:
        f.write("\n".join(txt_data))


if __name__ == "__main__":
    if argv[1] == "-f" or argv[1] == "--free":
        freeProxies()
    else:
        main()
