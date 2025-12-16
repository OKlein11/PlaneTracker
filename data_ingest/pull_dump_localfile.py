## For pulling the /aircraft.json file over the network then passing it to the flask app
import requests
import os
import json

def main():
    with open(os.path.join("","run","dump1090-fa","aircraft.json")) as f:
        data = json.load(f)
    
    requests.post("127.0.0.1:5000/add_dump", data=data)



if __name__ == "__main__":
    main()