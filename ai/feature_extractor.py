import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ProductFeature:
    name: str
    value: str
    unit: Optional[str] = None
    confidence: float = 1.0

class FeatureExtractor:
    def __init__(self, language: str = "ru"):
        self.language = language
        
        # Регулярные выражения для извлечения характеристик
        self.patterns = {
            "memory": [
                r"(\d+)\s*(ГБ|GB)",
                r"(\d+)\s*(ТБ|TB)",
                r"(\d+)\s*(МБ|MB)",
            ],
            "screen_size": [
                r"(\d+[.,]\d+)\s*(дюйм|inch|\")",
                r"(\d+[.,]\d+)\s*\"",
            ],
            "resolution": [
                r"(\d+)\s*x\s*(\d+)",
                r"(\d+)\s*на\s*(\d+)",
            ],
            "camera": [
                r"(\d+)\s*(Мп|MP)",
                r"(\d+)\s*мегапиксел",
            ],
            "battery": [
                r"(\d+)\s*(мАч|mAh)",
            ],
            "color": [
                r"цвет\s*:\s*([а-яА-Я]+)",
                r"колір\s*:\s*([а-яА-Яії]+)",
                r"color\s*:\s*([a-zA-Z]+)",
            ],
        }
        
        # Словари для нормализации единиц измерения
        self.unit_normalizers = {
            "ГБ": "GB",
            "МБ": "MB",
            "ТБ": "TB",
            "Мп": "MP",
            "мАч": "mAh",
            "дюйм": "inch",
        }
    
    def extract_features(self, text: str) -> List[ProductFeature]:
        """
        Извлекает характеристики товара из текста
        
        Args:
            text (str): Описание товара
            
        Returns:
            List[ProductFeature]: Список найденных характеристик
        """
        features = []
        
        # Ищем все характеристики по шаблонам
        for feature_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if feature_type == "resolution":
                        value = f"{match.group(1)}x{match.group(2)}"
                        unit = "pixels"
                    else:
                        value = match.group(1)
                        unit = match.group(2) if len(match.groups()) > 1 else None
                        
                    # Нормализуем единицы измерения
                    if unit in self.unit_normalizers:
                        unit = self.unit_normalizers[unit]
                        
                    features.append(ProductFeature(
                        name=feature_type,
                        value=value,
                        unit=unit
                    ))
        
        return features 