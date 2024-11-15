import requests

cookies = 'protocolstr=aHR0cHM=; iorChgSw=WQ==; test=aW5pdA; myGameVer_36239994=XzIxMTIyOA==; CookieChk=WQ; ft_myGame_36239994=e30=; login_36239994=MTczMTU2Mjg2NA; PID=RVlvcEoyWCUyRnFJakVHeSUyQnNRUlpSUVBXOWs1V1lKY0I2Z09hZng4Q0l3d3dpJTJCcU1SSnBBck51UTRlbGdRU2NIdW9UQXgxV2RFcjUxTkg2R0lQNXNIbGYlMkY2c1d3WWxEOHd0dUd6MElERHVzTSUzRA==; UID=ZHR5YzBsRE0w; cu=Tg==; cuipv6=Tg==; ipv6=Tg=='

headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Content-type': 'application/x-www-form-urlencoded',
    'Cookie': cookies,
    'Origin': 'https://64.188.38.107',
    'Referer': 'https://64.188.38.107/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

params = {
    'ver': '2024-11-13-no144_59',
}

data = {
    'uid': '0r5xov0yjtm36239994l77764b0',
    'ver': '2024-11-13-no144_59',
    'langx': 'en-us',
    'p': 'get_game_more',
    'gtype': 'ft',
    'showtype': 'live',
    'ltype': '4',
    'isRB': 'Y',
    'lid': '102812',
    'specialClick': '',
    'mode': 'NORMAL',
    'filter': 'Main',
    'ts': '1731548913044',
    'ecid': '8837592',
}

response = requests.post(
    'https://64.188.38.107/transform.php',
    params=params,
    headers=headers,
    data=data,
    verify=False,
)
print(response.text)