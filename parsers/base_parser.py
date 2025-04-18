from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
from datetime import datetime
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

@dataclass
class ProductPrice:
    value: float
    currency: str
    timestamp: datetime = datetime.now()

@dataclass
class ProductInfo:
    title: str
    description: str
    url: str
    price: Optional[ProductPrice] = None
    images: List[str] = None
    available: bool = True
    specifications: Dict[str, str] = None

class BaseParser(ABC):
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        self.browser = None
        self.context = None
        self.playwright = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        
        # Запускаем браузер с дополнительными параметрами
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # Запускаем в headless режиме
            args=[
                '--disable-blink-features=AutomationControlled',  # Отключаем определение автоматизации
                '--disable-dev-shm-usage',  # Исправляем проблемы с памятью в Docker
                '--no-sandbox',  # Отключаем песочницу для производительности
                '--disable-setuid-sandbox',
                '--disable-gpu',  # Отключаем GPU для стабильности
                '--disable-infobars',  # Отключаем информационные сообщения
                '--window-size=1920,1080',  # Устанавливаем размер окна
                '--start-maximized',  # Максимизируем окно
                '--ignore-certificate-errors',  # Игнорируем ошибки сертификатов
            ]
        )
        
        # Создаем контекст с дополнительными параметрами
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.ua.random,
            ignore_https_errors=True,
            java_script_enabled=True,
            bypass_csp=True,  # Отключаем CSP для обхода некоторых ограничений
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        )
        
        # Устанавливаем параметры геолокации для Украины (Киев)
        await self.context.set_geolocation({"latitude": 50.4501, "longitude": 30.5234})
        
        # Устанавливаем разрешения
        await self.context.grant_permissions(['geolocation'])
        
        # Эмулируем устройство
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    @abstractmethod
    async def parse_product_page(self, url: str) -> ProductInfo:
        """
        Парсит страницу товара
        
        Args:
            url (str): URL страницы товара
            
        Returns:
            ProductInfo: Информация о товаре
        """
        pass
    
    @abstractmethod
    async def search_products(self, query: str, limit: int = 10) -> List[str]:
        """
        Ищет товары по запросу
        
        Args:
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            
        Returns:
            List[str]: Список URL товаров
        """
        pass
    
    async def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Загружает страницу и создает объект BeautifulSoup
        
        Args:
            url (str): URL страницы
            
        Returns:
            Optional[BeautifulSoup]: Объект BeautifulSoup или None в случае ошибки
        """
        try:
            page = await self.context.new_page()
            
            # Устанавливаем обработчики для диалоговых окон
            page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))
            
            # Отключаем загрузку изображений и стилей для ускорения
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
            
            # Загружаем страницу с таймаутом
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Прокручиваем страницу для загрузки динамического контента
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
            # Получаем HTML
            html = await page.content()
            await page.close()
            
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            print(f"Ошибка при загрузке страницы {url}: {e}")
            return None
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Очищает текст от лишних пробелов и переносов строк
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    @staticmethod
    def extract_price(text: str) -> Optional[ProductPrice]:
        """
        Извлекает цену из текста
        
        Args:
            text (str): Текст с ценой
            
        Returns:
            Optional[ProductPrice]: Объект с ценой или None
        """
        if not text:
            return None
            
        # Ищем число с разделителем тысяч и копеек
        price_match = re.search(r'([\d\s.,]+)\s*(₴|грн|₽|руб|$|€|UAH|RUB|USD|EUR)', text)
        if price_match:
            # Очищаем число от пробелов и правильно обрабатываем разделители
            price_str = re.sub(r'[^\d.,]', '', price_match.group(1))
            price_str = price_str.replace(',', '.')
            
            # Конвертируем в число
            try:
                price = float(price_str)
                currency = price_match.group(2)
                
                # Нормализуем валюту
                currency_map = {
                    '₴': 'UAH',
                    'грн': 'UAH',
                    '₽': 'RUB',
                    'руб': 'RUB',
                    '$': 'USD',
                    '€': 'EUR'
                }
                
                return ProductPrice(
                    value=price,
                    currency=currency_map.get(currency, currency)
                )
            except ValueError:
                return None
                
        return None 