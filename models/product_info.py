from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ProductInfo:
    """Класс для хранения информации о товаре"""
    title: str
    price: Optional[float]
    description: str
    images: List[str]
    specifications: Dict[str, str]
    available: bool
    url: str 