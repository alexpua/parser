import asyncio
from parsers.store_specific.rozetka_parser import RozetkaParser

async def main():
    parser = RozetkaParser()
    print("Поиск товаров по запросу: iPhone 15")
    results = await parser.search_products("iPhone 15", limit=5)
    
    if results:
        print("\nНайденные товары:")
        for product in results:
            print(f"\nНазвание: {product['title']}")
            print(f"Цена: {product['price']} грн")
            print(f"URL: {product['url']}")
            print(f"Изображение: {product['image_url']}")
    else:
        print("Товары не найдены")

if __name__ == "__main__":
    asyncio.run(main()) 