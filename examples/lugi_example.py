import asyncio
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.store_specific.lugi_parser import LUGIParser
from utils.log import logger

async def main():
    # Создаем экземпляр парсера
    parser = LUGIParser()
    
    # Пример поиска товаров
    search_query = "гриль"
    logger.info(f"Ищем товары по запросу: {search_query}")
    
    # Получаем список URL товаров
    product_urls = await parser.search_products(search_query, limit=5)
    
    if not product_urls:
        logger.warning("Товары не найдены")
        return
    
    logger.info("\nНайденные URL товаров:")
    for i, url in enumerate(product_urls, 1):
        logger.info(f"{i}. {url}")
    logger.info("---\n")
    
    # Парсим каждый найденный товар
    for i, url in enumerate(product_urls):
        logger.info(f"\nПарсим информацию о продукте: {url}")
        product = await parser.parse_product_page(url)
        if product:
            if i == 0:  # Для первого продукта выводим полную информацию
                logger.info("Полная информация о продукте:")
                logger.info(product)
                
                logger.info("\nПодробная информация о продукте:")
                logger.info(f"Название: {product.title}")
                logger.info(f"Цена: {product.price}")
                logger.info(f"Описание: {product.description}")
                logger.info(f"Характеристики: {product.specifications}")
                logger.info(f"Изображения: {product.images}")
                logger.info(f"Доступность: {'В наличии' if product.available else 'Нет в наличии'}")
                logger.info(f"URL: {product.url}")
            else:  # Для остальных продуктов выводим только основную информацию
                logger.info(f"Найден товар: {product.title}")
                logger.info(f"Цена: {product.price}")
                logger.info(f"Доступность: {'В наличии' if product.available else 'Нет в наличии'}")
                logger.info(f"URL: {product.url}")
                logger.info("---")

if __name__ == "__main__":
    asyncio.run(main()) 