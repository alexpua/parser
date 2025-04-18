import asyncio
import json
import logging
from typing import Dict, List, Any
import aiohttp
from bs4 import BeautifulSoup
from ..base_parser import BaseParser

logger = logging.getLogger('parser')

class AmazonParser(BaseParser):
    """Парсер для интернет-магазина Amazon"""
    
    BASE_URL = "https://www.amazon.com"
    
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
            
            # Формируем URL для поиска
            search_url = f"{self.BASE_URL}/s"
            params = {
                'k': query,
                'ref': 'nb_sb_noss'
            }
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка при поиске: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Ищем карточки товаров
                    product_cards = soup.select('div[data-component-type="s-search-result"]')[:limit]
                    
                    products = []
                    for card in product_cards:
                        try:
                            # Получаем основную информацию о товаре
                            title_elem = card.select_one('h2 a span')
                            price_elem = card.select_one('span.a-price-whole')
                            link_elem = card.select_one('h2 a')
                            image_elem = card.select_one('img.s-image')
                            
                            if not all([title_elem, link_elem]):
                                continue
                            
                            # Формируем данные о товаре
                            product = {
                                'title': title_elem.text.strip(),
                                'price': float(price_elem.text.replace(',', '')) if price_elem else 0,
                                'url': self.BASE_URL + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href'],
                                'images': [image_elem['src']] if image_elem else [],
                                'availability': 'available'  # Amazon обычно показывает только доступные товары в поиске
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
                    title = soup.select_one('#productTitle')
                    price = soup.select_one('#priceblock_ourprice, #priceblock_dealprice')
                    description = soup.select_one('#productDescription p')
                    availability = soup.select_one('#availability span')
                    image_gallery = soup.select('#altImages img')
                    
                    # Получаем характеристики товара
                    specs = {}
                    specs_table = soup.select('#productDetails_techSpec_section_1 tr')
                    for row in specs_table:
                        label = row.select_one('.label')
                        value = row.select_one('.value')
                        if label and value:
                            specs[label.text.strip()] = value.text.strip()
                    
                    # Формируем результат
                    result = {
                        'title': title.text.strip() if title else '',
                        'price': float(price.text.replace('$', '').replace(',', '')) if price else 0,
                        'description': description.text.strip() if description else '',
                        'specifications': specs,
                        'availability': availability.text.strip() if availability else 'unknown',
                        'images': [img['src'] for img in image_gallery if 'src' in img.attrs]
                    }
                    
                    return result
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы товара: {str(e)}")
            return {} 