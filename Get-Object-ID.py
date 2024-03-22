from flask import Flask, request, jsonify
from re import compile, search
from json import loads, dumps
from typing import Literal
import requests
import re
app = Flask(__name__)
FIND_POSTID_PATTERN = compile(r',"post_id":"(\d+)",')
FIND_USERID_PATTERN = compile(r',"userID":"(\d+)",')
FIND_GROUPID_PATTERN = compile(r'{"groupID":"(\d+)",')
FIND_FEEDBACK_ID_PATTERN1 = compile(r'","feedback_id":"([^"]+)",')
FIND_FEEDBACK_ID_PATTERN = compile(r'"parent_feedback":{"id":"([^"]+)",')


def ParseCookies(cookies) -> list:
    cookies = cookies.replace(" ", "").strip()
    cookieList = []
    for cookie in cookies.split("\n"):
        cookie = dict(
            [
                (cookieItem.split("=")[0], cookieItem.split("=")[1])
                for cookieItem in cookie.split(";")
                if cookieItem != ""
            ]
        )
        cookieList.append(cookie)
    return cookieList


def RevertCookies(cookies: object):
    if "value" not in str(cookies):
        return ";".join(
            [f"{list(cookie)[0]}={list(cookie)[1]}" for cookie in cookies.items()]
        )
    else:
        return ";".join(
            [f'{cookie.get("name")}={cookie.get("value")}' for cookie in cookies]
        )


def ParseEmPassCookies(cookies: str) -> list:
    if "|" not in cookies:
        return ParseCookies(
            "\n".join(
                [
                    cookie.split(":")[-1]
                    for cookie in cookies.strip().replace("\n\n", "").split("\n")
                ]
            )
        )
    else:
        return ParseCookies(
            "\n".join(
                [
                    cookie.split("|")[-1]
                    for cookie in cookies.strip().replace("\n\n", "").split("\n")
                ]
            )
        )


def FormatJson(
    results: str,
    formatType: Literal[
        "To Cookies Array",
        "To Email:Pass",
        "To Line Cookies",
        "To Email:Pass:Cookies",
        "From Line : Seperated Cookies To Email:Pass",
        "From Line | Seperated Cookies To Email:Pass",
        "From Line : Seperated Cookies To Cookies",
        "From : Seperated To Email",
        "From : Seperated To Password",
    ] = "To Cookies Array",
):
    results = results.strip()
    results.replace("|:", "|").replace(":|", "|")
    if formatType == "To Cookies Array":
        if "{" in str(results):
            results = results.strip()
            resArray = []
            for result in results.split("\n"):
                try:
                    resArray.append(loads(result.replace("'", '"')).get("cookies"))
                except:
                    pass
            return dumps(resArray)
        elif len(str(results.strip().split("\n")[0]).split(":")) == 3:
            return dumps(ParseEmPassCookies(str(results)))
        else:
            return dumps(ParseCookies(results))
    elif formatType == "To Email:Pass":
        resArray = []
        for result in results.split("\n"):
            try:
                JSON = loads(result.replace("'", '"'))
                resArray.append(f'{JSON["email"]}:{JSON["password"]}')
            except:
                pass
        return "\n".join(resArray)
    elif formatType == "To Line Cookies":
        resArray = []
        for result in loads(results):
            try:
                resArray.append(f"{RevertCookies(result)}")
            except:
                pass
        return "\n".join(resArray)
    elif formatType == "To Email:Pass:Cookies":
        resArray = []
        for result in results.split("\n"):
            try:
                JSON = loads(result.replace("'", '"'))
                resArray.append(
                    f'{JSON["email"]}:{JSON["password"]}:{RevertCookies(JSON["cookies"])}'
                )
            except:
                pass
        return "\n".join(resArray)
    elif formatType == "From Line : Seperated Cookies To Email:Pass":
        resArray = []
        for result in results.split("\n"):
            try:
                result = result.split(":")
                resArray.append(f"{result[0]}:{result[1]}")
            except:
                pass
        return "\n".join(resArray)
    elif formatType == "From Line | Seperated Cookies To Email:Pass":
        resArray = []
        for result in results.split("\n"):
            try:
                result = result.split("|")
                resArray.append(f"{result[0]}")
            except:
                pass
        return "\n".join(resArray)
    elif formatType == "From Line To Cookies":
        resArray = []
        for result in results.split("\n"):
            try:
                res = result.split(":")
                if len(res) <= 2:
                    res = result.split("|")
                resArray.append(f"{res[-1]}")
            except:
                pass
        return "\n".join(resArray)
    elif formatType == "From : Seperated To Email":
        resArray = []
        for result in results.split("\n"):
            try:
                res = result.split(":")
                resArray.append(f"{res[0]}")
            except:
                pass
        return "\n".join(resArray)
    elif formatType == "From : Seperated To Password":
        resArray = []
        for result in results.split("\n"):
            try:
                res = result.split(":")
                resArray.append(f"{res[1]}")
            except:
                pass
        return "\n".join(resArray)


def GetObjectID(url: str, cookies: dict):
    headers = {
        "authority": "www.facebook.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        # 'cookie': 'ps_l=0; ps_n=0; sb=vD65ZQBuunm4S0ntAJ-82bUo; datr=qgqOZUwzBVqBEHfUVOFg3Tf4; sb=qgqOZbRUandDZ2XzGZU4Vqg_; c_user=61554370335382; xs=22%3AbAMN3AV8Vo2wyw%3A2%3A1703807659%3A-1%3A-1; fr=0nfj4ogdJQiz3GuES.AWW4cKZ1sX37Zw_l8Mxp-G4_tiI.Bljgqq.x7.AAA.0.0.Bljgqq.AWWlkpgjG3k; m_page_voice=61554370335382; dpr=0.8999999761581421; fr=01z60uG8ho3Vm4UAW.AWWzqccXsgUtEk4g1ziizKWsTR0.BluT68.x7.AAA.0.0.BluT7C.AWUJCSnm_Cc; presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1706639061459%2C%22v%22%3A1%7D; wd=927x712',
        "dpr": "0.9",
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-full-version-list": '"Not_A Brand";v="8.0.0.0", "Chromium";v="120.0.6099.227", "Google Chrome";v="120.0.6099.227"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"10.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport-width": "928",
    }
    headers["referer"] = url
    response = requests.get(url, cookies=cookies, headers=headers)
    HTML = response.text
    try:
        return search(FIND_USERID_PATTERN, HTML).group(1)
    except:
        try:
            return search(FIND_POSTID_PATTERN, HTML).group(1)
        except:
            try:
                return search(FIND_GROUPID_PATTERN, HTML).group(1)
            except:
                return "Couldn't Be Found"

@app.route("/GetID", methods=["GET"])
def GetID():
    url = request.args.get("url")
    cookiesStr = re.search(r'cookies=([^&]+)', request.query_string.decode("utf-8","ignore")).group(1)
    if not url:
        return jsonify({"error": "URL parameter is missing"}), 400
    if not cookiesStr:
        return jsonify({"error": "Cookies parameter is missing"}), 400
    try:
        cookies = eval(FormatJson(cookiesStr))[0]
    except Exception as e:
        return ({"error": "Invalid Cookie Provided","details":f"{e}","cookies":f"{cookiesStr}","queryString": request.query_string.decode("utf-8","ignore")}), 400
    id = GetObjectID(url, cookies)
    return jsonify({"id": id})
@app.route("/", methods=["GET"])
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Get Facebook ID Test Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 0;
        }

        .container {
            max-width: 600px;
            margin: 100px auto;
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 36px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        label {
            font-size: 18px;
            color: #555;
        }

        input[type="text"] {
            width: calc(100% - 20px);
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #69b3e7;
        }

        button[type="submit"] {
            background-color: #007bff;
            color: #fff;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        button[type="submit"]:hover {
            background-color: #0056b3;
        }

        #result {
            margin-top: 20px;
            font-size: 18px;
            color: #333;
        }
        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        #status {
         padding: 5px;
         text-align: center;
        }
        .animated {
            animation-duration: 1s;
            animation-fill-mode: both;
            animation-timing-function: ease-in-out;
            animation-name: fadeIn;
        }

        .fetched-id {
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
            transition: background-color 0.3s;
        }

        .fetched-id:hover {
            background-color: #e9e9e9;
        }

        .fetching {
            color: #007bff;
        }

        .failed-id {
            color: red;
        }
    </style>
</head>
<body>
    <div class="container animated">
        <h1>Get Facebook ID Test Page</h1>
        <form id="myForm">
            <label for="url">URL:</label>
            <input type="text" id="url" name="url"><br><br>
            <label for="cookies">Cookies:</label>
            <input type="text" id="cookies" name="cookies" value="ps_l=0;datr=d437ZaunRz-UkRxmKrjL7ppo;m_page_voice=61551892817543;fr=0BHl3f7XqTZHS8802.AWWljysXh2psX8vqdZQ7Rsj40E8.Bl-417..AAA.0.0.Bl-419.AWVSO5_8R1c;presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1710984578178%2C%22v%22%3A1%7D;c_user=61551892817543;datr=ivnkZZNbqcsgcGEcGHZipkMl;fr=0MrbljZo8mXmyf3nB.AWUGyaaTKZyvX5DKfmJkUT3BgDM.Bl5PmK..AAA.0.0.Bl5PmK.AWX4-0KnpjI;ps_n=0;sb=d437ZZSxZvnEnQds5kkLx0Qa;sb=ivnkZRt_deXv3vJDbgr3CUag;wd=1366x651;xs=12%3AVO8Ro76UAe3w9g%3A2%3A1709504907%3A-1%3A-1"><br><br>
            <button type="submit">Submit</button>
        </form>
        <div id="status">Status: IDLE</div>
        <div id="result"></div>
    </div>

    <script>
      document.getElementById("myForm").addEventListener("submit", function(event) {
          event.preventDefault();
          var url = document.getElementById("url").value;
          var cookies = document.getElementById("cookies").value;
          var resultContainer = document.getElementById("result");
          var statusElement = document.getElementById("status")
          statusElement.innerHTML = "Status: Fetching ID...";
          var xhr = new XMLHttpRequest();
          xhr.open("GET", "/GetID?url=" + encodeURIComponent(url) + "&cookies=" + cookies, true);
          xhr.onreadystatechange = function() {
              if (xhr.readyState == XMLHttpRequest.DONE) {
                  if (xhr.status == 200) {
                      var response = JSON.parse(xhr.responseText);
                      var ul = document.createElement("ul");
                      if (Array.isArray(response)) {
                          response.forEach(function(id) {
                              var li = document.createElement("li");
                              li.classList.add("fetched-id");
                              if (id === undefined || id === "Couldn't Be Found") {
                                  li.innerText = "ID: Couldn't Be Found";
                                  li.classList.add("failed-id");
                              } else {
                                  li.innerText = "ID: " + id;
                              }
                              ul.appendChild(li);
                          });
                      } else {
                          var li = document.createElement("li");
                          li.classList.add("fetched-id");
                          if (response.id === undefined || response.id === "Couldn't Be Found") {
                              li.innerText = "ID: Couldn't Be Found";
                              li.classList.add("failed-id");
                          } else {
                              li.innerText = "ID: " + response.id;
                          }
                          ul.appendChild(li);
                      }
                      resultContainer.appendChild(ul);
                      statusElement.innerHTML = "Status: IDLE";
                  } else {
                      window.alert("Error:"+xhr.status.toString());
                      statusElement.innerHTML = "Status: IDLE";
                  }
              }
          };
          xhr.send();
      });
  </script>  
</body>
</html>
"""
