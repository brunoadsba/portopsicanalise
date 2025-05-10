from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List

class ContentCategory(Enum):
    FREUDIAN_CONCEPTS = "conceitos_freudianos"
    JUNG_THEORY = "teoria_junguiana"
    LACAN_CONCEPTS = "conceitos_lacanianos"
    PRACTICAL_TIPS = "dicas_praticas"
    REFLECTION = "reflexoes"

class ContentType(Enum):
    QUOTE = "citacao"
    CONCEPT = "conceito"
    QUESTION = "pergunta"
    TIP = "dica"

@dataclass
class Content:
    id: str  # UUID único
    title: str
    text: str  # Texto principal para a imagem
    caption: str  # Legenda completa para Instagram
    category: ContentCategory
    content_type: ContentType
    hashtags: List[str]
    image_path: Optional[str] = None
    created_at: datetime = datetime.now()
    posted: bool = False
    post_id: Optional[str] = None
