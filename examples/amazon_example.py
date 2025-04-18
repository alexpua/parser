import asyncio
import json
from parsers.store_specific.amazon_parser import AmazonParser

async def main():
    parser = AmazonParser()
    results = await parser.search_products("iPhone 15", limit=5)
    
    if results:
        print("Найдены товары:")
        for product in results:
            print(json.dumps(product, indent=2, ensure_ascii=False))
    else:
        print("Товары не найдены")

if __name__ == "__main__":
    asyncio.run(main()) 