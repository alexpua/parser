# Web Parser

Асинхронный парсер для различных интернет-магазинов.

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd parser
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Структура проекта

- `parsers/` - директория с парсерами
  - `base_parser.py` - базовый класс парсера
  - `store_specific/` - специфичные парсеры для разных магазинов

## Использование

```python
from parsers.store_specific.some_store_parser import SomeStoreParser

async def main():
    async with SomeStoreParser() as parser:
        # Поиск товаров
        products = await parser.search_products("query")
        
        # Парсинг страницы товара
        product_info = await parser.parse_product_page("product_url")

if __name__ == "__main__":
    asyncio.run(main())
```

## Добавление нового парсера

Для добавления парсера для нового магазина:

1. Создайте новый файл в директории `parsers/store_specific/`
2. Унаследуйте ваш класс от `BaseParser`
3. Реализуйте методы `parse_product_page` и `search_products`

## Лицензия

MIT 