import requests
import settings
import json
import os

api_url = "https://api.app.eolab.com/"

if not settings.username or not settings.password:
    print("Please set username and password in settings.py")

session = requests.session()

response = session.post(f"{api_url}signin/email", json={"email": settings.username, "password": settings.password})
response = response.json()["data"]

accessToken = response["accessToken"]
userId = response["id"]

headers = {
    "Authorization": f"Bearer {accessToken}"
}

body = {
    "dateTimeFilter": {
        "time":3,
        "customStartDate":"",
        "customEndDate":"",
        "customString":"ninety-days",
        "timezone":"Europe/Amsterdam"
    },
    "userId": userId
}
response = session.post(f"{api_url}swim/data/search?pageSize=10&pageNo=1&locale=en_US", headers=headers, json=body)
response = response.json()["data"]

totalPages = response["totalPages"]
for item in response["data"]["items"]:
    comments = " ".join(c["content"] for c in item["comments"])
    swimDate = item["swimDate"]
    swimId = item["swimId"]

    print(f"ID: {swimId} - {swimDate} (comments: {comments})")

swimId = input("Please enter ID of the swim you want to import: ")

response = session.get(f"{api_url}swim/data?locale=en_us&Id={swimId}", headers=headers, json=body)
response = response.json()["data"]
if not os.path.exists("data"):
    os.mkdir("data")

datadir = os.path.join("data", swimId)
if not os.path.exists(datadir):
    os.mkdir(datadir)

open(os.path.join(datadir, "data-data.json"), "w").write(json.dumps(response))


response = session.get(f"{api_url}swim/chart/lapforcetime-swim?locale=en_US&swimId={swimId}", headers=headers, json=body)
response = response.json()["data"]
open(os.path.join(datadir, "data-lapforcetime.json"), "w").write(response)

for lap in range(1, 3):
    response = session.get(f"{api_url}swim/chart/pathsweep?locale=en_US&swimId={swimId}&lap={lap}", headers=headers, json=body)
    response = response.json()["data"]
    open(os.path.join(datadir, f"data-pathsweep-{lap}.json"), "w").write(response)
    response = session.get(f"{api_url}swim/chart/pathdepth?locale=en_US&swimId={swimId}&lap={lap}", headers=headers, json=body)
    response = response.json()["data"]
    open(os.path.join(datadir, f"data-pathdepth-{lap}.json"), "w").write(response)
    response = session.get(f"{api_url}swim/chart/strokephase?locale=en_US&swimId={swimId}&lap={lap}", headers=headers, json=body)
    response = response.json()["data"]
    open(os.path.join(datadir, f"data-strokephase-{lap}.json"), "w").write(response)
