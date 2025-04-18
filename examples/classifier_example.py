from ai.classifier import ProductClassifier
import json

def analyze_product(description: str, language: str = "ru"):
    """
    Анализирует описание товара на указанном языке
    
    Args:
        description (str): Описание товара
        language (str): Язык описания ("ru" или "uk")
    """
    # Создаем экземпляр классификатора
    classifier = ProductClassifier(language=language)
    
    print(f"\nАнализ товара ({language.upper()}):")
    print("-" * 50)
    print(f"Описание: {description.strip()}")
    print("-" * 50)
    
    # Анализируем товар
    result = classifier.analyze_product(description)
    
    # Выводим результаты
    print(f"Категория: {result['category']}")
    print("-" * 50)
    
    print("Характеристики:")
    for feature in result['features']:
        value_str = f"{feature['value']}"
        if feature['unit']:
            value_str += f" {feature['unit']}"
        print(f"- {feature['name']}: {value_str}")
    
    print("-" * 50)
    print("Дополнительные сущности:")
    for entity in result['entities']:
        print(f"- {entity['text']} ({entity['type']}, уверенность: {entity['score']:.2%})")

def main():
    # Пример на русском языке
    ru_description = """
    Смартфон Samsung Galaxy S21 с экраном 6.2 дюйма, 
    8 ГБ оперативной памяти, 128 ГБ встроенной памяти, 
    тройной камерой 64 Мп и процессором Exynos 2100.
    Разрешение экрана: 2400 x 1080.
    Батарея: 4000 мАч.
    Цвет: черный. Производство: Южная Корея.
    """
    analyze_product(ru_description, "ru")
    
    # Пример на украинском языке
    uk_description = """
    Смартфон Samsung Galaxy S21 з екраном 6.2 дюйма,
    8 ГБ оперативної пам'яті, 128 ГБ вбудованої пам'яті,
    потрійною камерою 64 Мп та процесором Exynos 2100.
    Роздільна здатність екрану: 2400 x 1080.
    Батарея: 4000 мАч.
    Колір: чорний. Виробництво: Південна Корея.
    """
    analyze_product(uk_description, "uk")

if __name__ == "__main__":
    main() 