from bs4 import BeautifulSoup
import re
from typing import Dict, Optional, Any, List
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger('parser')

class SmartParser:
    def __init__(self, storage_path: str = "data/patterns.json"):
        self.storage_path = storage_path
        self.patterns = self.load_patterns()
        
    def load_patterns(self) -> Dict:
        """Загрузка сохраненных паттернов"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка при загрузке паттернов: {e}")
        return {
            "price": [],
            "title": [],
            "model": [],
            "brand": [],
            "availability": []
        }
    
    def save_patterns(self):
        """Сохранение паттернов в файл"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении паттернов: {e}")

    def get_selector_path(self, element) -> str:
        """Получение CSS-селектора для элемента"""
        if not element:
            return ""
            
        parts = []
        while element and element.name:
            # Получаем имя тега
            current = element.name
            
            # Добавляем классы
            if element.get('class'):
                current += '.' + '.'.join(element.get('class'))
                
            # Добавляем id
            if element.get('id'):
                current += f"#{element.get('id')}"
                
            parts.append(current)
            element = element.parent
            
        return ' > '.join(reversed(parts))

    def discover_patterns(self, html: str) -> Dict[str, List[str]]:
        """Поиск новых паттернов в HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        new_patterns = {
            "price": [],
            "title": [],
            "model": [],
            "brand": [],
            "availability": []
        }
        
        # Поиск цен
        price_candidates = soup.find_all(
            text=re.compile(r'\d+[\s,.]?\d*\s*(?:грн|₴)')
        )
        for candidate in price_candidates:
            selector = self.get_selector_path(candidate.parent)
            if selector and selector not in self.patterns["price"]:
                new_patterns["price"].append(selector)
        
        # Поиск названий товаров
        title_candidates = soup.find_all(['h1', 'h2', '.product-name'])
        for candidate in title_candidates:
            selector = self.get_selector_path(candidate)
            if selector and selector not in self.patterns["title"]:
                new_patterns["title"].append(selector)
        
        # Поиск моделей
        model_candidates = soup.find_all(
            text=re.compile(r'(?:Модель|Артикул):\s*[A-Za-z0-9-]+')
        )
        for candidate in model_candidates:
            selector = self.get_selector_path(candidate.parent)
            if selector and selector not in self.patterns["model"]:
                new_patterns["model"].append(selector)
        
        # Поиск брендов
        brand_candidates = soup.find_all(
            text=re.compile(r'(?:Виробник|Бренд):\s*[A-Za-z]+')
        )
        for candidate in brand_candidates:
            selector = self.get_selector_path(candidate.parent)
            if selector and selector not in self.patterns["brand"]:
                new_patterns["brand"].append(selector)
        
        # Поиск наличия
        availability_candidates = soup.find_all(
            text=re.compile(r'[Вв]\s*наявності|[Нн]емає в наявності')
        )
        for candidate in availability_candidates:
            selector = self.get_selector_path(candidate.parent)
            if selector and selector not in self.patterns["availability"]:
                new_patterns["availability"].append(selector)
        
        return new_patterns

    def extract_data(self, html: str) -> Dict[str, Any]:
        """Извлечение данных с использованием известных паттернов"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        # Извлекаем цену
        for selector in self.patterns["price"]:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                price_clean = ''.join(c for c in price_text if c.isdigit())
                if price_clean:
                    data["price"] = float(price_clean)
                    break
        
        # Извлекаем название
        for selector in self.patterns["title"]:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    data["title"] = title
                    break
        
        # Извлекаем модель
        for selector in self.patterns["model"]:
            element = soup.select_one(selector)
            if element:
                model_text = element.get_text(strip=True)
                model_match = re.search(r'(?:Модель|Артикул):\s*([A-Za-z0-9-]+)', model_text)
                if model_match:
                    data["model"] = model_match.group(1)
                    break
        
        # Извлекаем бренд
        for selector in self.patterns["brand"]:
            element = soup.select_one(selector)
            if element:
                brand_text = element.get_text(strip=True)
                brand_match = re.search(r'(?:Виробник|Бренд):\s*([A-Za-z]+)', brand_text)
                if brand_match:
                    data["brand"] = brand_match.group(1)
                    break
        
        # Извлекаем наличие
        for selector in self.patterns["availability"]:
            element = soup.select_one(selector)
            if element:
                availability_text = element.get_text(strip=True).lower()
                data["available"] = "наявності" in availability_text
                break
        
        return data

    def learn(self, html: str, success_data: Dict[str, Any]):
        """Обучение на успешном парсинге"""
        new_patterns = self.discover_patterns(html)
        
        # Добавляем новые паттерны
        for field, patterns in new_patterns.items():
            self.patterns[field].extend(patterns)
            
        # Удаляем дубликаты
        for field in self.patterns:
            self.patterns[field] = list(set(self.patterns[field]))
        
        # Сохраняем обновленные паттерны
        self.save_patterns()
        
        logger.info(f"Добавлены новые паттерны: {new_patterns}")

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Валидация извлеченных данных"""
        rules = {
            "price": lambda x: isinstance(x, (int, float)) and x > 0,
            "title": lambda x: isinstance(x, str) and len(x) > 5,
            "model": lambda x: isinstance(x, str) and bool(re.match(r'^[A-Za-z0-9-]+$', x)),
            "brand": lambda x: isinstance(x, str) and len(x) > 1,
            "available": lambda x: isinstance(x, bool)
        }
        
        return all(
            key not in data or rules[key](data[key])
            for key in rules
        ) 