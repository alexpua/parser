from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import re
from ..base_parser import BaseParser, ProductInfo, ProductPrice
import urllib.parse
import asyncio
import json
import requests
from utils.log import logger
from playwright.async_api import async_playwright
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

class RozetkaParser(BaseParser):
    """Парсер для интернет-магазина Rozetka"""
    
    BASE_URL = "https://rozetka.com.ua"
    API_URL = "https://rozetka.com.ua/api/product-api/v4/goods/get-main"
    
    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Настройка Chrome
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')  # Запуск в фоновом режиме
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
    
    async def search_products(self, query: str, limit: int = 5) -> List[Dict]:
        """Поиск товаров по запросу"""
        try:
            logger.info(f"Начинаем поиск по запросу: {query}")
            
            # Формируем параметры запроса
            params = {
                'front-type': 'xl',
                'country': 'UA',
                'lang': 'ru',
                'text': query,
                'page': 1,
                'per_page': limit
            }
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.API_URL, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка API: {response.status}")
                        return []
                    
                    data = await response.json()
                    logger.info(f"API Response: {json.dumps(data, indent=2)}")
                    
                    if not data.get('data', {}).get('goods'):
                        logger.warning("Не найдены товары в ответе API")
                        return []
                    
                    products = []
                    for good in data['data']['goods']:
                        try:
                            product = {
                                'title': good.get('title', ''),
                                'price': good.get('price', 0),
                                'url': good.get('href', ''),
                                'images': [good.get('main_image', '')],
                                'availability': 'available' if good.get('sell_status') == 'available' else 'unavailable'
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
    
    def _clean_price(self, price_str: str) -> Optional[float]:
        """Очистка и преобразование строки с ценой в число"""
        try:
            # Удаляем все символы кроме цифр и точки
            clean_price = re.sub(r'[^\d.]', '', price_str)
            return float(clean_price)
        except (ValueError, TypeError):
            return None
    
    async def parse_product_page(self, url: str) -> ProductInfo:
        """
        Парсит страницу товара на Rozetka
        
        Args:
            url (str): URL страницы товара
            
        Returns:
            ProductInfo: Информация о товаре
        """
        print(f"\nПарсинг страницы товара: {url}")
        
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(5)  # Даем время на загрузку динамического контента
            
            # Получаем название
            title = None
            for selector in ['.product__title', '.product-header__title']:
                element = await page.query_selector(selector)
                if element:
                    title = await element.text_content()
                    title = self.clean_text(title)
                    break
            
            # Получаем описание
            description = ""
            for selector in ['.product-about__description', '.product-about__description-content']:
                element = await page.query_selector(selector)
                if element:
                    description = await element.text_content()
                    description = self.clean_text(description)
                    break
            
            # Получаем цену
            price = None
            for selector in ['.product-price__big', '.product-price__value']:
                element = await page.query_selector(selector)
                if element:
                    price_text = await element.text_content()
                    price = self.extract_price(price_text)
                    if price:
                        break
            
            # Получаем изображения
            images = []
            for selector in ['.product-photo__picture img', '.product__photo img']:
                elements = await page.query_selector_all(selector)
                for img in elements:
                    src = await img.get_attribute('src')
                    if src:
                        images.append(src)
            
            # Получаем характеристики
            specifications = {}
            for selector in ['.characteristics-full__item', '.product-characteristics__item']:
                spec_elements = await page.query_selector_all(selector)
                for spec in spec_elements:
                    name_element = await spec.query_selector('.characteristics-full__name, .product-characteristics__name')
                    value_element = await spec.query_selector('.characteristics-full__value, .product-characteristics__value')
                    
                    if name_element and value_element:
                        name = await name_element.text_content()
                        value = await value_element.text_content()
                        name = self.clean_text(name)
                        value = self.clean_text(value)
                        specifications[name] = value
            
            # Проверяем наличие
            available = False
            for selector in ['.product-status--available', '.product__status--green']:
                element = await page.query_selector(selector)
                if element:
                    available = True
                    break
            
            return ProductInfo(
                title=title,
                description=description,
                url=url,
                price=price,
                images=images,
                available=available,
                specifications=specifications
            )
            
        except Exception as e:
            print(f"Ошибка при парсинге товара: {e}")
            return None
        finally:
            await page.close() 