## For pulling the /aircraft.json file over the network then passing it to the flask app
import requests


def main():
    data= requests.get("http://google.com")
    print(data.content)
    data = requests.get("http://192.168.110.76:30005")
    print(data.content)



if __name__ == "__main__":
    main()