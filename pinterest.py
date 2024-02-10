from aiohttp import ClientSession
from urllib.parse import urlencode
from copy import deepcopy
import json, time
import aiofiles
import os
from contextlib import suppress


PINTEREST_API = "https://www.pinterest.com"
SEARCH_ENDPOINT = PINTEREST_API + "/resource/BaseSearchResource/get/"



async def get_csrf():
    """ Получение CSRF токена. """
    async with ClientSession() as session:
        async with session.get(PINTEREST_API) as response:
            # Получаем от сайта какие куки установить 
            cookies = response.headers.getall("Set-Cookie")
            csrf_token = cookies[0].split(";")[0].split("=")[-1] # csrf-token
            return csrf_token


async def download_pin(url: str, path: str):
    async with ClientSession() as session:
        async with session.get(url=url) as response:
            async with aiofiles.open(path, "wb") as file:
                await file.write(await response.content.read())


async def search_pins(query: str):
    """ Функция для поиска пинов """
    
    params = {
        "source_url":f"/search/pins/{urlencode({'q':query})}",
        "data":{
            "options":{
                "query":query,  
                "scope":"pins",
            },
            "context":{},
        },
        '_': '%s' % int(time.time() * 1000)
    }
    
    
    params_json = deepcopy(params)
    params_json["data"] = json.dumps(params_json["data"])
    
    url = SEARCH_ENDPOINT + "?" + urlencode(params_json).replace("+", "%20")
    
    csrf_token = await get_csrf()
    
    headers = {
        "X-Pinterest-Source-Url":f"/search/pins/{urlencode({'q':query})}",
        "X-Csrftoken":csrf_token,
    }
    
    cookies = {
        "csrftoken":csrf_token
    }
    with suppress(FileExistsError):
        os.mkdir(query)
    
    async with ClientSession(headers=headers, cookies=cookies) as session:
        async with session.get(url=url) as response:
            json_data = await response.json()
            bookmark = json_data.get("resource_response").get("bookmark")
            params["data"]["options"]["bookmarks"] = [bookmark]
            results = json_data.get("resource_response").get("data").get("results")
            for res in results:
                original_image = res.get("images").get("orig")
                original_image_url = original_image.get("url")
                await download_pin(url=original_image_url, path=f"{query}\\{original_image_url.split('/')[-1]}")
        while True:
            params_json = deepcopy(params)
            params_json["data"] = json.dumps(params_json["data"])
            async with session.post(SEARCH_ENDPOINT, json=params_json) as response:
                json_data = await response.json()
                results = json_data.get("resource_response").get("data").get("results")
                for res in results:
                    original_image = res.get("images").get("orig")
                    original_image_url = original_image.get("url")
                    await download_pin(url=original_image_url, path=f"{query}\\{original_image_url.split('/')[-1]}")
                bookmark = json_data.get("resource_response").get("bookmark")
                params["data"]["options"]["bookmarks"] = [bookmark]
            print("\n\n")
            