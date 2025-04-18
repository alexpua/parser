from enum import Enum
from typing import Dict, List

class ProductCategory(Enum):
    SMARTPHONE = "smartphone"
    LAPTOP = "laptop"
    TV = "tv"
    TABLET = "tablet"
    HEADPHONES = "headphones"
    UNKNOWN = "unknown"

class CategoryMatcher:
    def __init__(self):
        self.category_keywords = {
            ProductCategory.SMARTPHONE: [
                "смартфон", "телефон", "smartphone", "phone",
                "iphone", "android", "мобильный"
            ],
            ProductCategory.LAPTOP: [
                "ноутбук", "laptop", "нетбук", "macbook",
                "ultrabook", "ультрабук"
            ],
            ProductCategory.TV: [
                "телевизор", "tv", "смарт тв", "smart tv",
                "монитор", "monitor"
            ],
            ProductCategory.TABLET: [
                "планшет", "tablet", "ipad", "galaxy tab"
            ],
            ProductCategory.HEADPHONES: [
                "наушники", "headphones", "earbuds", "airpods",
                "гарнитура", "headset"
            ]
        }
        
        # Добавляем украинские ключевые слова
        self.uk_category_keywords = {
            ProductCategory.SMARTPHONE: [
                "смартфон", "телефон", "мобільний"
            ],
            ProductCategory.LAPTOP: [
                "ноутбук", "нетбук", "ультрабук"
            ],
            ProductCategory.TV: [
                "телевізор", "монітор"
            ],
            ProductCategory.TABLET: [
                "планшет"
            ],
            ProductCategory.HEADPHONES: [
                "навушники", "гарнітура"
            ]
        }
    
    def match_category(self, text: str, language: str = "ru") -> ProductCategory:
        """
        Определяет категорию товара по описанию
        
        Args:
            text (str): Описание товара
            language (str): Язык описания ("ru" или "uk")
            
        Returns:
            ProductCategory: Категория товара
        """
        text = text.lower()
        
        # Выбираем словарь ключевых слов в зависимости от языка
        keywords = self.uk_category_keywords if language == "uk" else self.category_keywords
        
        # Ищем совпадения с ключевыми словами
        for category, words in keywords.items():
            if any(word in text for word in words):
                return category
                
        return ProductCategory.UNKNOWN 