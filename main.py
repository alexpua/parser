import asyncio
from LUGIParser import LUGIParser
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    parser = LUGIParser()
    search_query = "LUGI"
    products = await parser.search_products(search_query)
    
    print(f"Найдено {len(products)} товаров:")
    for product in products:
        print(f"Название: {product['name']}")
        print(f"URL: {product['url']}")
        print(f"Цена: {product['price']}")
        print("-" * 50)
    
    # Парсим первый продукт для примера
    if products:
        url = products[0]['url']
        print(f"\nПарсим информацию о продукте: {url}")
        product = await parser.parse_product_page(url)
        
        # Логируем весь объект product
        logging.info("Полная информация о продукте:")
        logging.info(product)
        
        print("\nПодробная информация о продукте:")
        print(f"Название: {product['name']}")
        print(f"Цена: {product['price']}")
        print(f"Описание: {product['description']}")
        print(f"Характеристики: {product['specifications']}")
        print(f"Изображения: {product['images']}")
        print(f"Доступность: {product['availability']}")
        print(f"Артикул: {product['sku']}")
        print(f"Категория: {product['category']}")
        print(f"Бренд: {product['brand']}")
        print(f"Рейтинг: {product['rating']}")
        print(f"Количество отзывов: {product['reviews_count']}")
        print(f"URL: {product['url']}")
        print(f"Дополнительная информация: {product['additional_info']}")

if __name__ == "__main__":
    asyncio.run(main()) 