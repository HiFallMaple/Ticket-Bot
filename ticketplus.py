import threading
import time
import requests
import json
from crypto import decrypt
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

req = requests.Session()
CRYPTED_EVENTID = "54fdee72c71c18cc2b694801e11e77cd"
COUNT = 1
ENABLE_TICKET_AREA = True

headers = {
    "authority": "apis.ticketplus.com.tw",
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,tr;q=0.6,ja;q=0.5,zh-CN;q=0.4",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://ticketplus.com.tw",
    "referer": "https://ticketplus.com.tw/",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def get_timestamp() -> str:
    return str(int(time.time() * 1000))


def get_login_payload() -> dict:
    with open("account.json", "r", encoding="utf-8") as file:
        return json.load(file)


def verify_token(token: str) -> bool:
    params = {
        "_": get_timestamp(),
    }
    json_data = {
        "token": token,
    }
    response = req.post(
        "https://apis.ticketplus.com.tw/user/api/v1/token",
        params=params,
        headers=headers,
        json=json_data,
    )
    result = json.loads(response.text)
    return result["errCode"] == "00"


def get_by_sortedIndex(sortedIndex: int, list: list) -> dict:
    print(list)
    for i in list:
        if i["sortedIndex"] == sortedIndex:
            return i
    raise Exception("sortedIndex not found")


def get_ticket_area_info(products: dict):
    params = {
        "ticketAreaId": ",".join([i["ticketAreaId"] for i in products["products"]]),
        "productId": ",".join([i["productId"] for i in products["products"]]),
        "_": get_timestamp(),
    }
    response = requests.get(
        "https://apis.ticketplus.com.tw/config/api/v1/get",
        params=params,
        headers=headers,
    )
    data = json.loads(response.text)
    return data


def print_ticket_area_info(products: dict):
    data = get_ticket_area_info(products)
    print(data)
    for i in data["result"]["ticketArea"]:
        print("ticketAreaName:", i["ticketAreaName"], end="")
        print(", price:", i["price"], end="")
        if "count" in i:
            print(", count:", i["count"])
        else:
            print()


def reserve_ticket(
    productId: str, captcha_key: str, captcha: str, ticket_area_name: str = None
):
    params = {
        "_": get_timestamp(),
    }
    json_data = {
        "products": [
            {
                "productId": productId,
                "count": COUNT,
            },
        ],
        "captcha": {
            "key": captcha_key,
            "ans": captcha,
        },
        "consecutiveSeats": True,
        "finalizedSeats": True,
        "reserveSeats": True,
    }
    while True:
        time.sleep(1)
        response = req.post(
            "https://apis.ticketplus.com.tw/ticket/api/v1/reserve",
            params=params,
            headers=headers,
            json=json_data,
        )
        data = json.loads(response.text)
        if ENABLE_TICKET_AREA:
            print(f"{ticket_area_name}: ", end="")
        print(f"{data}")
        if data["errCode"] == "00" or data["errCode"] == "111":
            return


def start_reserve(products: dict):
    product = products["products"][0]
    crypted_sessionId = product["sessionId"]
    params = {
        "_": get_timestamp(),
    }

    json_data = {
        "refresh": False,
        "sessionId": decrypt(crypted_sessionId),
    }

    response = req.post(
        "https://apis.ticketplus.com.tw/captcha/api/v1/generate",
        params=params,
        headers=headers,
        json=json_data,
    )
    data = json.loads(response.text)
    captcha_key = data["key"]
    with open("output.svg", "w") as f:
        f.write(str(data["data"]))
    captcha = input("Please input captcha: ")

    threads = []
    for i in range(len(products["products"])):
        thread = threading.Thread(
            target=reserve_ticket,
            args=(
                products["products"][i]["productId"],
                captcha_key,
                captcha,
                ticket_area_name[i],
            ),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


# login
params = {
    "_": get_timestamp(),
}

json_data = get_login_payload()

response = req.post(
    "https://apis.ticketplus.com.tw/user/api/v1/login",
    params=params,
    headers=headers,
    json=json_data,
)
token = json.loads(response.text)["userInfo"]["access_token"]
headers["Authorization"] = f"Bearer {token}"


# get events info
response = req.get(
    f"https://apis.ticketplus.com.tw/config/api/v1/getS3?path=event/{CRYPTED_EVENTID}/sessions.json",
    headers=headers,
)

# 使用 sortedIndex 區分場次
data = json.loads(response.text)
for i in data["sessions"]:
    print(i)


# get productId, sessionId
response = req.get(
    f"https://apis.ticketplus.com.tw/config/api/v1/getS3?path=event/{CRYPTED_EVENTID}/products.json",
    headers=headers,
)
products = json.loads(response.text)
for i in products["products"]:
    print(i)

# ticketAreas
if ENABLE_TICKET_AREA:
    print_ticket_area_info(products)
    ticket_area_name = [
        i["ticketAreaName"]
        for i in get_ticket_area_info(products)["result"]["ticketArea"]
    ]


# 建立一個阻塞式調度器
scheduler = BlockingScheduler()

# 設定任務在 2023/12/26 的 21:15 執行
scheduler.add_job(
    start_reserve, "date", run_date=datetime(2023, 12, 26, 21, 18, 0), args=(products,)
)

# 啟動調度器
scheduler.start()
