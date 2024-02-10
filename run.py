import asyncio
import logging

from pinterest import search_pins, get_csrf


async def main():
    
    query = input("Enter query >> ")
    
    await search_pins(query=query)


if __name__ == "__main__":
    asyncio.run(main())
