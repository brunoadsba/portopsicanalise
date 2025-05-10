import logging
from pathlib import Path
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import yaml

# Importar o modelo Content e os Enums
from ..models.content import Content, ContentCategory, ContentType

class CreatorAgent:
    def __init__(self, templates_dir: str, output_dir: str, knowledge_base_path: str, 
                 use_ai_generation: bool = False, api_key: Optional[str] = None, 
                 image_generator: Optional[Any] = None):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base: Optional[Dict[str, Any]] = self._load_knowledge_base()
        
        self.use_ai_generation = use_ai_generation
        self.api_key = api_key
        self.image_generator = image_generator

        # Configurações básicas de logging para o agente
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info(f"CreatorAgent inicializado. Templates: {self.templates_dir}, Output: {self.output_dir}")

    def _load_knowledge_base(self) -> Optional[Dict[str, Any]]:
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Arquivo da base de conhecimento não encontrado: {self.knowledge_base_path}")
            return None
        except Exception as e:
            self.logger.error(f"Erro ao carregar a base de conhecimento: {e}")
            return None

    def create_content(self, category: Optional[ContentCategory] = None, 
                       content_type_filter: Optional[ContentType] = None) -> Optional[Content]:
        """
        Cria uma nova peça de conteúdo.
        Esta é uma implementação esqueleto. A lógica detalhada será adicionada depois.
        """
        self.logger.info(f"Solicitação para criar conteúdo. Categoria: {category}, Tipo: {content_type_filter}")
        if not self.knowledge_base or not self.knowledge_base.get("conceitos"):
            self.logger.error("Base de conhecimento não carregada ou vazia. Impossível criar conteúdo.")
            return None

        import random
        selected_kb_item = random.choice(self.knowledge_base["conceitos"])
        
        actual_category = category or ContentCategory.REFLECTION
        actual_content_type = content_type_filter or ContentType.CONCEPT
        
        image_text = selected_kb_item.get("descricao_curta", "Texto para imagem")
        caption_text = selected_kb_item.get("descricao", "Legenda completa.")
        title = selected_kb_item.get("nome", "Título do Conteúdo")

        hashtags = ["#psicanalise", "#exemplo"]

        content_id = str(uuid.uuid4())
        
        image_path = None

        new_content = Content(
            id=content_id,
            title=title,
            text=image_text,
            caption=caption_text,
            category=actual_category,
            content_type=actual_content_type,
            hashtags=hashtags,
            image_path=image_path,
            created_at=datetime.now(),
            posted=False,
            post_id=None
        )
        
        self.logger.info(f"Conteúdo esqueleto criado: {new_content.id} - {new_content.title}")
        return new_content

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    script_dir = Path(__file__).parent
    temp_assets_dir = script_dir / "temp_assets" / "templates"
    temp_output_dir = script_dir / "temp_output" / "images"
    kb_dummy_path = script_dir / "temp_knowledge_base.yaml"

    temp_assets_dir.mkdir(parents=True, exist_ok=True)
    temp_output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(kb_dummy_path, 'w', encoding='utf-8') as f:
        yaml_content = """
conceitos:
  - nome: "Inconsciente Esqueleto"
    descricao_curta: "O psíquico real (esqueleto)"
    descricao: "O inconsciente é uma parte da mente que opera fora da consciência (esqueleto)."
    categorias: ["conceitos_freudianos"]
  - nome: "Complexo de Édipo Esqueleto"
    descricao_curta: "Desejos infantis (esqueleto)"
    descricao: "Conflito central na teoria psicanalítica sobre desejos na infância (esqueleto)."
    categorias: ["conceitos_freudianos"]
"""
        f.write(yaml_content)

    import sys
    sys.path.append(str(script_dir.parent.parent))
    from models.content import Content, ContentCategory, ContentType

    creator = CreatorAgent(
        templates_dir=str(temp_assets_dir),
        output_dir=str(temp_output_dir),
        knowledge_base_path=str(kb_dummy_path)
    )
    
    novo_conteudo = creator.create_content(category=ContentCategory.FREUDIAN_CONCEPTS)
    if novo_conteudo:
        print(f"Conteúdo Gerado: {novo_conteudo}")
    else:
        print("Falha ao gerar conteúdo.")
    
    kb_dummy_path.unlink()
    for f in temp_output_dir.glob('*'): f.unlink()
    temp_output_dir.rmdir()
    (temp_output_dir.parent).rmdir()

    for f in temp_assets_dir.glob('*'): f.unlink()
    temp_assets_dir.rmdir()
    (temp_assets_dir.parent).rmdir()
