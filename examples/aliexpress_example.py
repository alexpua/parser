import asyncio
import json
from parsers.store_specific.aliexpress_parser import AliExpressParser

async def main():
    parser = AliExpressParser()
    results = await parser.search_products("iPhone 15", limit=5)
    
    if results:
        print("Найдены товары:")
        for product in results:
            print(json.dumps(product, indent=2, ensure_ascii=False))
            
            # Получаем детальную информацию о товаре
            details = await parser.parse_product_page(product['url'])
            if details:
                print("\nДетальная информация:")
                print(json.dumps(details, indent=2, ensure_ascii=False))
                print("\n" + "="*50 + "\n")
    else:
        print("Товары не найдены")

if __name__ == "__main__":
    asyncio.run(main()) 