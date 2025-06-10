import asyncio
import json
from enum import IntEnum

import aiofiles
import httpx
from pydantic import BaseModel


class Price(BaseModel):
    basic: int
    product: int
    total: int
    logistics: int


class Size(BaseModel):
    name: str
    origName: str
    optionId: int
    price: Price


class Product(BaseModel):
    id: int
    name: str
    brand: str
    brandId: int
    supplier: str
    supplierId: int
    rating: float
    sizes: list[Size]


class Location(IntEnum):
    MOSCOW = -1257786
    SAINT_PETERSBURG = -1257786
    NOVOSIBIRSK = -364763


class WildberriesParser:
    async def search(self, query: str, location: int, number_of_pages: int):
        process_page_tasks = [
            asyncio.create_task(self._parse_page(query, location, page_number))
            for page_number in range(1, number_of_pages + 1)
        ]
        for process_page_task in asyncio.as_completed(process_page_tasks):
            products = await process_page_task
            for product in products:
                yield product

    async def _parse_page(self, query: str, location: int, page_number: int):
        url = "https://search.wb.ru:443/exactmatch/ru/common/v11/search"
        params = {
            "ab_testing": "false",
            "appType": "32",
            "curr": "rub",
            "dest": str(location),
            "hide_dtype": "13",
            "lang": "ru",
            "locale": "ru",
            "page": str(page_number),
            "query": "+".join(query.split()),
            "resultset": "catalog",
            "sort": "popular",
            "spp": "30",
            "suppressSpellcheck": "false",
        }
        headers = {
            "X-Queryid": "qid1000555564448345352120250610160815",
            "Wb-AppReferer": "CatalogSI",
            "Wb-AppType": "android",
            "Wb-AppVersion": "716",
            "Site-Locale": "ru",
            "WB-AppLanguage": "ru",
            "devicename": "Android, Android SDK built for arm64(sdk_gphone64_arm64)",
            "deviceId": "ff287eb05b4c3044",
            "serviceType": "FB",
            "deviceToken": "ezoLwFEkTRaqqpKSCLUGgQ:APA91bGKZ0fq31jz-Wp74v3uHm4OMKE1wEFtKlOm2TmvuP95RgpeI-snTaItNWIwEPCXSA8IX9bm8rSupBB1E45Z-Ab0XlkgJiqyqlfaHyN-4Xl_EIbobjg",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "okhttp/4.12.6-wb",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=30)
            raw_products = response.json()["data"]["products"]
            return [Product(**raw_product) for raw_product in raw_products]


async def main():
    query = "платье летнее"
    location = Location.MOSCOW
    number_of_pages = 30
    parser = WildberriesParser()
    async with aiofiles.open("products.jsonl", "w", encoding="utf-8") as f:
        async for product in parser.search(query, location, number_of_pages):
            await f.write(json.dumps(product.model_dump(), ensure_ascii=False) + "\n")


asyncio.run(main())
