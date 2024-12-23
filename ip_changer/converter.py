import json
from turtle import st
from typing import List

from attr import dataclass

@dataclass
class Proxy:
    country: str
    ping: str
    protocol: str
    anonymityLevel: str
    address: str
    

def main():
    json_file = "./proxies.json"
    unique=[]
    seen=set()
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
            

if __name__ == "__main__":
    main()