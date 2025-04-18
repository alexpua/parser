import asyncio
import json
import logging
from typing import Dict, List, Any
import aiohttp
from bs4 import BeautifulSoup
from ..base_parser import BaseParser

logger = logging.getLogger('parser')

class AliExpressParser(BaseParser):
    """Парсер для интернет-магазина AliExpress"""
    
    BASE_URL = "https://aliexpress.com"
    SEARCH_URL = "https://www.aliexpress.com/wholesale"
    
    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
    
    async def search_products(self, query: str, limit: int = 5) -> List[Dict]:
        """Поиск товаров по запросу"""
        try:
            logger.info(f"Начинаем поиск по запросу: {query}")
            
            # Формируем параметры запроса
            params = {
                'SearchText': query,
                'page': 1,
                'g': 'y',  # Показывать только товары с бесплатной доставкой
                'sortType': 'total_tranpro_desc'  # Сортировка по популярности
            }
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.SEARCH_URL, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка при поиске: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Ищем карточки товаров
                    product_cards = soup.select('div.product-card')[:limit]
                    
                    products = []
                    for card in product_cards:
                        try:
                            # Получаем основную информацию о товаре
                            title_elem = card.select_one('h1.product-title')
                            price_elem = card.select_one('div.product-price')
                            link_elem = card.select_one('a.product-card__link')
                            image_elem = card.select_one('img.product-img')
                            
                            if not all([title_elem, price_elem, link_elem]):
                                continue
                            
                            # Очищаем цену от символов валюты и форматирования
                            price_text = price_elem.text.strip()
                            price = float(price_text.replace('US $', '').replace(',', ''))
                            
                            # Формируем данные о товаре
                            product = {
                                'title': title_elem.text.strip(),
                                'price': price,
                                'url': link_elem['href'] if link_elem['href'].startswith('http') else self.BASE_URL + link_elem['href'],
                                'images': [image_elem['src']] if image_elem and 'src' in image_elem.attrs else [],
                                'availability': 'available'  # AliExpress обычно показывает только доступные товары
                            }
                            
                            products.append(product)
                            logger.info(f"Найден товар: {product['title']}")
                            
                        except Exception as e:
                            logger.error(f"Ошибка при обработке товара: {str(e)}")
                            continue
                    
                    return products
            
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров: {str(e)}")
            return []
    
    async def parse_product_page(self, url: str) -> Dict[str, Any]:
        """Парсинг страницы товара"""
        try:
            logger.info(f"Парсим страницу товара: {url}")
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка при получении страницы товара: {response.status}")
                        return {}
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Получаем основную информацию о товаре
                    title = soup.select_one('h1.product-title')
                    price = soup.select_one('div.product-price')
                    description = soup.select_one('div.product-description')
                    specs = soup.select('div.specification-table tr')
                    images = soup.select('div.images-view-list img')
                    
                    # Собираем характеристики товара
                    specifications = {}
                    for row in specs:
                        label = row.select_one('th')
                        value = row.select_one('td')
                        if label and value:
                            specifications[label.text.strip()] = value.text.strip()
                    
                    # Формируем результат
                    result = {
                        'title': title.text.strip() if title else '',
                        'price': float(price.text.replace('US $', '').replace(',', '')) if price else 0,
                        'description': description.text.strip() if description else '',
                        'specifications': specifications,
                        'availability': 'available',  # AliExpress обычно показывает только доступные товары
                        'images': [img['src'] for img in images if 'src' in img.attrs]
                    }
                    
                    return result
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы товара: {str(e)}")
            return {} 