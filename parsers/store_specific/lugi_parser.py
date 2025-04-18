import asyncio
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import urllib.parse
import json
import re

from parsers.base_parser import BaseParser
from models.product_info import ProductInfo
from utils.log import logger
from parsers.smart_parser import SmartParser

class LUGIParser(BaseParser):
    BASE_URL = "https://lugi.com.ua"
    SEARCH_URL = f"{BASE_URL}/search/"
    API_URL = f"{BASE_URL}/index.php?route=product/product/get_product_data"
    
    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.smart_parser = SmartParser()

    async def search_products(self, query: str, limit: int = 10) -> List[str]:
        """
        Поиск товаров на сайте LUGI
        """
        logger.info(f"Начинаем поиск по запросу: {query}")
        product_urls = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                # Формируем URL для поиска с правильным кодированием
                encoded_query = urllib.parse.quote(query)
                search_url = f"{self.SEARCH_URL}?search={encoded_query}"
                logger.info(f"Поисковый URL: {search_url}")
                
                # Загружаем страницу поиска
                await page.goto(search_url)
                await page.wait_for_load_state("networkidle")
                
                # Получаем HTML страницы
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # Ищем все карточки товаров по обновленному селектору
                product_cards = soup.select(".product-layout")
                logger.info(f"Найдено карточек товаров: {len(product_cards)}")
                
                for card in product_cards[:limit]:
                    # Пробуем найти ссылку в разных местах карточки
                    product_link = None
                    
                    # Проверяем ссылку в изображении
                    image_link = card.select_one(".image a")
                    if image_link and image_link.get("href"):
                        product_link = image_link
                        
                    # Если не нашли в изображении, ищем в названии
                    if not product_link:
                        name_link = card.select_one(".product-name a")
                        if name_link and name_link.get("href"):
                            product_link = name_link
                    
                    if product_link and product_link.get("href"):
                        url = product_link["href"]
                        if not url.startswith("http"):
                            url = self.BASE_URL + url
                        product_urls.append(url)
                        logger.info(f"Добавлен URL товара: {url}")
                    else:
                        logger.warning(f"Не удалось найти ссылку на товар в карточке")
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке страницы {search_url}: {str(e)}")
            return []
            
        return product_urls

    async def parse_product_page(self, url: str) -> Optional[ProductInfo]:
        """
        Парсинг страницы товара
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                # Загружаем страницу и ждем загрузки контента
                await page.goto(url)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_load_state("domcontentloaded")
                
                # Ждем появления основных элементов
                await page.wait_for_selector(".product-name", timeout=10000)
                await page.wait_for_selector(".price", timeout=10000)
                
                # Даем время на загрузку динамического контента
                await page.wait_for_timeout(2000)
                
                # Получаем HTML страницы
                content = await page.content()
                
                # Сначала пробуем использовать стандартный парсинг
                data = await self._standard_parse(content)
                
                # Если стандартный парсинг не дал результатов, пробуем SmartParser
                if not data or not any(data.values()):
                    smart_data = self.smart_parser.extract_data(content)
                    if smart_data and self.smart_parser.validate_data(smart_data):
                        data = smart_data
                else:
                    # Если стандартный парсинг успешен, обучаем SmartParser
                    self.smart_parser.learn(content, data)
                
                await browser.close()
                
                if data:
                    # Проверяем наличие товара по кнопке "Купить"
                    soup = BeautifulSoup(content, "html.parser")
                    buy_button = soup.select_one("#button-cart")
                    available = bool(buy_button and not "disabled" in buy_button.get("class", []))
                    
                    # Очищаем цену от нечисловых символов, если она есть
                    price = data.get("price")
                    if isinstance(price, str):
                        price = float(''.join(c for c in price if c.isdigit() or c == '.'))
                    
                    return ProductInfo(
                        title=data.get("title", "").strip(),
                        price=price,
                        description=data.get("description", "").strip(),
                        images=data.get("images", []),
                        specifications=data.get("specifications", {}),
                        available=available,
                        url=url
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы {url}: {str(e)}")
            return None

    async def _standard_parse(self, content: str) -> Dict[str, Any]:
        """Стандартный метод парсинга"""
        soup = BeautifulSoup(content, "html.parser")
        data = {}
        
        # Получаем название товара (пробуем разные селекторы)
        title_selectors = [
            "h1.product-name",
            "h1.product-title",
            "h1.name",
            "h1[itemprop='name']",
            ".product-name h1",
            "#product h1"
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                data["title"] = title_element.get_text(strip=True)
                break
        
        # Получаем цену
        price_element = soup.select_one(".autocalc-product-price")
        if price_element:
            price_text = price_element.get_text(strip=True)
            price_clean = ''.join(c for c in price_text if c.isdigit())
            if price_clean:
                data["price"] = float(price_clean)
        
        # Получаем описание
        description_element = soup.select_one("#tab-description")
        if description_element:
            for element in description_element.select("script, style"):
                element.decompose()
            data["description"] = description_element.get_text(strip=True)
        
        # Получаем изображения
        images = []
        main_image = soup.select_one(".image a img")
        if main_image:
            for attr in ["data-additional-hover", "src"]:
                src = main_image.get(attr)
                if src:
                    if not src.startswith("http"):
                        src = self.BASE_URL + src
                    images.append(src)
                    break
        
        additional_images = soup.select(".additional-images img")
        for img in additional_images:
            for attr in ["data-additional-hover", "src"]:
                src = img.get(attr)
                if src:
                    if not src.startswith("http"):
                        src = self.BASE_URL + src
                    if src not in images:
                        images.append(src)
                    break
        
        data["images"] = images
        
        # Получаем характеристики
        specs = {}
        specs_table = soup.select("#tab-specification tr")
        for row in specs_table:
            cells = row.select("td")
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if name and value:
                    specs[name] = value
        
        data["specifications"] = specs
        
        # Проверяем наличие
        stock_element = soup.select_one(".stock-status")
        if stock_element:
            stock_text = stock_element.get_text(strip=True).lower()
            data["available"] = "в наявності" in stock_text or "в наличии" in stock_text
        
        return data

    def _get_text(self, element) -> str:
        """Получение текста из элемента с обработкой None"""
        return element.get_text(strip=True) if element else ""

    def _extract_price(self, price_element) -> Optional[float]:
        """Извлечение цены из элемента"""
        if not price_element:
            return None
            
        try:
            price_text = price_element.get_text(strip=True)
            # Удаляем все символы кроме цифр и точки
            price_clean = ''.join(c for c in price_text if c.isdigit() or c == '.')
            return float(price_clean)
        except (ValueError, AttributeError):
            return None 