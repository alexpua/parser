from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
from typing import List, Dict, Optional, Tuple
from .product_categories import CategoryMatcher, ProductCategory
from .feature_extractor import FeatureExtractor, ProductFeature

class ProductClassifier:
    def __init__(self, language: str = "ru"):
        """
        Инициализация классификатора
        
        Args:
            language (str): Язык для классификации ("ru" или "uk")
        """
        self.language = language
        
        # Выбор модели в зависимости от языка
        if language == "uk":
            model_name = "xlm-roberta-base"  # Используем многоязычную модель
        else:
            model_name = "cointegrated/rubert-tiny2"
            
        # Инициализация модели для классификации
        self.classifier = pipeline(
            "text-classification",
            model=model_name,
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Инициализация модели для извлечения характеристик
        self.ner = pipeline(
            "token-classification",
            model="xlm-roberta-large",
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Загрузка токенизатора для работы с текстом
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Инициализация дополнительных компонентов
        self.category_matcher = CategoryMatcher()
        self.feature_extractor = FeatureExtractor(language)
    
    def analyze_product(self, product_description: str) -> Dict:
        """
        Полный анализ товара: категория, характеристики, сущности
        
        Args:
            product_description (str): Описание товара
            
        Returns:
            Dict: Результаты анализа
        """
        # Определяем категорию
        category = self.category_matcher.match_category(product_description, self.language)
        
        # Извлекаем характеристики
        features = self.feature_extractor.extract_features(product_description)
        
        # Получаем дополнительные сущности через NER
        try:
            entities = self.ner(product_description)
            ner_features = [
                {
                    "text": entity["word"],
                    "type": entity["entity_group"],
                    "score": round(entity["score"], 3)
                }
                for entity in entities
            ]
        except Exception as e:
            print(f"Ошибка при извлечении сущностей: {e}")
            ner_features = []
        
        # Формируем результат
        result = {
            "category": category.value,
            "features": [
                {
                    "name": f.name,
                    "value": f.value,
                    "unit": f.unit,
                    "confidence": f.confidence
                }
                for f in features
            ],
            "entities": ner_features
        }
        
        return result

    def classify_product(self, product_description: str) -> Dict[str, float]:
        """
        Классифицирует товар на основе его описания
        
        Args:
            product_description (str): Описание товара
            
        Returns:
            Dict[str, float]: Словарь с вероятностями категорий
        """
        try:
            result = self.classifier(product_description)
            return result[0]
        except Exception as e:
            print(f"Ошибка при классификации: {e}")
            return {"label": "unknown", "score": 0.0}

    def extract_features(self, product_description: str) -> List[Dict[str, str]]:
        """
        Извлекает ключевые характеристики из описания товара
        
        Args:
            product_description (str): Описание товара
            
        Returns:
            List[Dict[str, str]]: Список характеристик с их типами
        """
        try:
            # Токенизация текста
            tokens = self.tokenizer(product_description, return_tensors="pt")
            
            # Извлечение сущностей
            entities = self.ner(product_description)
            
            # Обработка результатов
            features = []
            for entity in entities:
                feature = {
                    "text": entity["word"],
                    "type": entity["entity_group"],
                    "score": round(entity["score"], 3)
                }
                
                # Дополнительная обработка для специфических характеристик
                if "ГБ" in feature["text"] or "GB" in feature["text"]:
                    feature["type"] = "memory"
                elif "дюйм" in feature["text"] or "inch" in feature["text"]:
                    feature["type"] = "screen_size"
                elif "камера" in feature["text"] or "camera" in feature["text"]:
                    feature["type"] = "camera"
                    
                features.append(feature)
                
            return features
        except Exception as e:
            print(f"Ошибка при извлечении характеристик: {e}")
            return [] 