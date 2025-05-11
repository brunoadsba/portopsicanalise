import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import yaml
import random # Importado para o topo
from textwrap import wrap # Importado para o topo

# Importar o modelo Content e os Enums
from ..models.content import Content, ContentCategory, ContentType

# Importar componentes do Pillow
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # O logger ainda não está definido aqui, logaremos a ausência do Pillow no __init__

class CreatorAgent:
    def __init__(self, templates_dir: str, output_dir: str, knowledge_base_path: str, 
                 use_ai_generation: bool = False, api_key: Optional[str] = None, 
                 image_generator: Optional[Any] = None):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_dir = self.templates_dir / "fonts" # Caminho para fontes
        self.backgrounds_dir = self.templates_dir / "backgrounds" # Caminho para backgrounds

        # Adicionar caminho para a raiz do projeto e para o logo da marca d'água
        self.project_root = Path(__file__).resolve().parent.parent.parent # Vai para portopsicanalise/
        self.watermark_logo_image_path = self.project_root / "logo" / "logo_bg.png" # Caminho para sua imagem de marca d'água

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

        if not PIL_AVAILABLE:
            self.logger.warning("Pillow (PIL) não está instalado. Geração de imagem será desabilitada.")
        
        self.fonts: Dict[str, Optional[ImageFont.FreeTypeFont]] = self._load_fonts()
        self.color_palettes: Dict[ContentCategory, Dict[str, tuple]] = {
            ContentCategory.FREUDIAN_CONCEPTS: {"bg": (220, 230, 240), "text": (70, 85, 95)},      # Azul Suave
            ContentCategory.JUNG_THEORY: {"bg": (225, 235, 220), "text": (80, 95, 85)},          # Verde Suave
            ContentCategory.LACAN_CONCEPTS: {"bg": (230, 225, 235), "text": (85, 75, 90)},     # Lilás Acinzentado Suave
            ContentCategory.PRACTICAL_TIPS: {"bg": (245, 240, 230), "text": (90, 80, 70)},     # Bege/Creme
            ContentCategory.REFLECTION: {"bg": (220, 225, 230), "text": (75, 80, 90)},        # Cinza-azulado claro para fundo, texto cinza escuro
        }
        # Paleta default revisada
        self.default_palette = {"bg": (240, 240, 240), "text": (60, 60, 60)} # Fundo cinza bem claro, texto cinza escuro

        self.logger.info(f"CreatorAgent inicializado. Templates: {self.templates_dir}, Output: {self.output_dir}")

    def _load_fonts(self) -> Dict[str, Optional[ImageFont.FreeTypeFont]]:
        fonts_loaded = {}
        if not PIL_AVAILABLE:
            return {'default_title': None, 'default_body': None, 'default_author': None}

        font_files = {
            'title': 'Montserrat-Bold.ttf', # CONFIRME ESTE NOME
            'body': 'Montserrat-Regular.ttf',   # CONFIRME ESTE NOME
            'author': 'Montserrat-Italic.ttf' # CONFIRME ESTE NOME
        }
        # Tentar carregar fontes da pasta assets/templates/fonts
        # Se não encontrar, tentar carregar fontes padrão do sistema (Pillow pode encontrá-las)
        for name, filename in font_files.items():
            try:
                font_path = self.fonts_dir / filename
                if font_path.exists():
                    fonts_loaded[name] = ImageFont.truetype(str(font_path), size=60 if name=='title' else 40)
                else: # Tentar carregar fonte do sistema
                    fonts_loaded[name] = ImageFont.truetype(filename, size=60 if name=='title' else 40)
                self.logger.info(f"Fonte '{name}' ({filename}) carregada.")
            except IOError:
                self.logger.warning(f"Fonte '{name}' ({filename}) não encontrada em {self.fonts_dir} ou no sistema. Usando fallback se possível.")
                fonts_loaded[name] = None # Marcar como não carregada
            except Exception as e:
                self.logger.error(f"Erro ao carregar fonte '{name}': {e}")
                fonts_loaded[name] = None
        
        # Adicionar um fallback para o corpo se nenhuma fonte for carregada
        if not any(fonts_loaded.values()): # Se nenhuma fonte foi carregada
             try:
                fonts_loaded['default_body'] = ImageFont.load_default() # Uma fonte bitmap muito básica
                self.logger.info("Nenhuma fonte TrueType carregada. Usando fonte default do Pillow para o corpo.")
             except Exception as e:
                self.logger.error(f"Não foi possível carregar nem a fonte default do Pillow: {e}")
                fonts_loaded['default_body'] = None

        return fonts_loaded
        
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

        # Selecionar item da base de conhecimento
        # TODO: Implementar lógica de seleção mais sofisticada (filtrar por categoria, tipo, evitar repetição)
        selected_kb_item = random.choice(self.knowledge_base["conceitos"])

        # Determinar categoria e tipo (simplificado)
        # Tenta usar a categoria do item da KB, se existir e for válida, senão usa o default ou o filtro.
        try:
            kb_category_str = selected_kb_item.get("categorias", ["reflexoes"])[0] # Pega a primeira categoria
            actual_category = ContentCategory(kb_category_str)
        except ValueError: # Se a string da KB não for um membro válido de ContentCategory
            actual_category = category or ContentCategory.REFLECTION
        
        actual_content_type = self._determine_content_type(selected_kb_item) or content_type_filter or ContentType.CONCEPT
        
        title = selected_kb_item.get("nome", "Título Indefinido")
        image_main_text = selected_kb_item.get("descricao_curta", title) # Texto para a imagem
        image_author_text = None
        
        if actual_content_type == ContentType.QUOTE and selected_kb_item.get("citacoes"):
            citation = random.choice(selected_kb_item["citacoes"])
            image_main_text = f'"{citation.get("texto", title)}"'
            image_author_text = citation.get("autor")

        # Gerar legenda (pode ser mais elaborada)
        caption_text = f"✨ {title} ✨\n\n{selected_kb_item.get('descricao', image_main_text)}"
        if image_author_text:
            caption_text += f"\n\n— {image_author_text}"
            if actual_content_type == ContentType.QUOTE and selected_kb_item.get("citacoes"):
                obra = selected_kb_item["citacoes"][0].get("obra") # Assumindo que a citação é a mesma
                if obra:
                    caption_text += f", {obra}"


        # Gerar hashtags
        hashtags = self._generate_hashtags(actual_category, actual_content_type, selected_kb_item.get("palavras_chave", []))

        content_id = str(uuid.uuid4())
        
        image_path = None
        if PIL_AVAILABLE: # Só tenta gerar imagem se Pillow estiver disponível
            image_elements = {
                "main_text": image_main_text,
                "author_text": image_author_text, # Pode ser None
                "title_text": title if actual_content_type != ContentType.QUOTE else None # Só mostra título se não for citação
            }
            image_path = self._generate_image_with_pillow(content_id, image_elements, actual_category)
        else:
            self.logger.warning("Geração de imagem pulada pois Pillow (PIL) não está disponível.")


        new_content = Content(
            id=content_id,
            title=title,
            text=image_main_text, # O texto principal que iria para a imagem
            caption=caption_text + "\n\n" + " ".join(f"#{h}" for h in hashtags), # Adiciona hashtags à legenda
            category=actual_category,
            content_type=actual_content_type,
            hashtags=hashtags,
            image_path=str(image_path) if image_path else None,
            created_at=datetime.now(),
        )
        
        self.logger.info(f"Conteúdo criado: {new_content.id} - {new_content.title}")
        if new_content.image_path:
            self.logger.info(f"Imagem gerada em: {new_content.image_path}")
        return new_content

    def _determine_content_type(self, kb_item: Dict[str, Any]) -> Optional[ContentType]:
        if kb_item.get("citacoes"): return ContentType.QUOTE
        if kb_item.get("perguntas"): return ContentType.QUESTION
        if kb_item.get("dicas"): return ContentType.TIP
        return ContentType.CONCEPT # Default

    def _generate_hashtags(self, category: ContentCategory, content_type: ContentType, keywords: List[str]) -> List[str]:
        base_hashtags = ["PortoPsicanalise", "Psicanalise", "SaudeMental"]
        
        category_map = {
            ContentCategory.FREUDIAN_CONCEPTS: ["Freud", "TeoriaFreudiana"],
            ContentCategory.JUNG_THEORY: ["Jung", "PsicologiaAnalitica"],
            ContentCategory.LACAN_CONCEPTS: ["Lacan", "TeoriaLacaniana"],
            ContentCategory.PRACTICAL_TIPS: ["DicasPsicologicas", "Autoconhecimento"],
            ContentCategory.REFLECTION: ["ReflexaoDiaria", "PensamentoCritico"],
        }
        content_type_map = {
            ContentType.QUOTE: ["Citacoes", "FrasesInspiradoras"],
            ContentType.CONCEPT: ["ConceitosPsicanaliticos", "AprenderPsicanalise"],
            ContentType.QUESTION: ["PsicanaliseResponde", "QuestioneSe"],
            ContentType.TIP: ["DicaDePsicologia", "BemEstarEmocional"],
        }
        
        generated_hashtags = base_hashtags
        generated_hashtags.extend(category_map.get(category, []))
        generated_hashtags.extend(content_type_map.get(content_type, []))
        
        # Adicionar palavras-chave do item da KB, formatando-as como hashtags
        for kw in keywords:
            hashtag_kw = kw.replace(" ", "").replace("-", "").capitalize()
            if hashtag_kw not in generated_hashtags: # Evitar duplicados exatos
                 generated_hashtags.append(hashtag_kw)
        
        return list(set(generated_hashtags)) # Remover duplicados quaisquer

    def _generate_image_with_pillow(self, content_id: str, elements: Dict[str, Optional[str]], category: ContentCategory) -> Optional[Path]:
        if not PIL_AVAILABLE:
            self.logger.error("Tentativa de gerar imagem com Pillow, mas a biblioteca não está disponível.")
            return None

        image_size = (1080, 1080)
        palette = self.color_palettes.get(category, self.default_palette)
        bg_color = palette["bg"]
        text_color = palette["text"] 

        background_image_path = None
        if self.backgrounds_dir.exists():
            available_bgs = list(self.backgrounds_dir.glob("*.png")) + \
                              list(self.backgrounds_dir.glob("*.jpg")) + \
                              list(self.backgrounds_dir.glob("*.jpeg"))
            if available_bgs:
                background_image_path = random.choice(available_bgs)
        
        try:
            if background_image_path:
                img = Image.open(background_image_path).convert("RGBA")
                img_w, img_h = img.size
                if img_w != image_size[0] or img_h != image_size[1]:
                    ratio_w = image_size[0] / img_w; ratio_h = image_size[1] / img_h
                    if ratio_w > ratio_h: new_w = image_size[0]; new_h = int(img_h * ratio_w)
                    else: new_h = image_size[1]; new_w = int(img_w * ratio_h)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    left = (new_w - image_size[0]) / 2; top = (new_h - image_size[1]) / 2
                    right = (new_w + image_size[0]) / 2; bottom = (new_h + image_size[1]) / 2
                    img = img.crop((left, top, right, bottom))
                
                overlay_alpha = 180 
                overlay = Image.new("RGBA", image_size, bg_color + (overlay_alpha,))
                img = Image.alpha_composite(img, overlay)
                img = img.convert("RGB")
            else:
                img = Image.new('RGB', image_size, color=bg_color)
            
            logo_watermark_layer = Image.new("RGBA", image_size, (0,0,0,0)) 
            logo_opacity_factor = 0.7 # LOGO COM 70% DE OPACIDADE (30% TRANSPARENTE) - MANTIDO

            if self.watermark_logo_image_path.exists():
                try:
                    self.logger.info(f"Tentando carregar logo para marca d'água de: {self.watermark_logo_image_path}")
                    wm_logo_img = Image.open(self.watermark_logo_image_path).convert("RGBA")
                    base_width = image_size[0] * 0.8 
                    w_percent = (base_width / float(wm_logo_img.size[0]))
                    h_size = int((float(wm_logo_img.size[1]) * float(w_percent)))
                    wm_logo_img_resized = wm_logo_img.resize((int(base_width), h_size), Image.Resampling.LANCZOS)
                    wm_w, wm_h = wm_logo_img_resized.size
                    pos_x_logo = (image_size[0] - wm_w) // 2
                    pos_y_logo = (image_size[1] - wm_h) // 2
                    
                    temp_logo_alpha = wm_logo_img_resized.split()[-1]
                    temp_logo_alpha = temp_logo_alpha.point(lambda p: int(p * logo_opacity_factor))
                    wm_logo_img_resized.putalpha(temp_logo_alpha)

                    logo_watermark_layer.paste(wm_logo_img_resized, (pos_x_logo, pos_y_logo), wm_logo_img_resized)
                    self.logger.info(f"Marca d'água com logo '{self.watermark_logo_image_path.name}' adicionada à camada.")

                    img_rgba_for_logo = img.convert("RGBA")
                    img_composited_with_logo = Image.alpha_composite(img_rgba_for_logo, logo_watermark_layer)
                    img = img_composited_with_logo.convert("RGB")
                except FileNotFoundError:
                    self.logger.error(f"ARQUIVO NÃO ENCONTRADO para logo de marca d'água: {self.watermark_logo_image_path}")
                except Exception as e_wm_logo:
                    self.logger.error(f"Erro ao carregar ou processar logo para marca d'água: {e_wm_logo}", exc_info=True)
            else:
                self.logger.warning(f"Arquivo do logo para marca d'água NÃO EXISTE em: {self.watermark_logo_image_path}")
            
            draw = ImageDraw.Draw(img) # Objeto draw para a imagem que já tem o logo (com sua opacidade)

            # --- TEXTO @portopsicanalise (inferior direito, 100% cor) ---
            try:
                handle_text_content = "@portopsicanalise"
                font_handle_text = self.fonts.get('author') or self.fonts.get('body') or ImageFont.load_default()
                font_handle_text = font_handle_text.font_variant(size=30) 
                handle_text_fill_color = text_color 
                padding_handle_text_x = 30 
                padding_handle_text_y = 120 
                try:
                    bbox_handle = draw.textbbox((0,0), handle_text_content, font=font_handle_text)
                    text_w_handle = bbox_handle[2] - bbox_handle[0]; text_h_handle = bbox_handle[3] - bbox_handle[1]
                except AttributeError: 
                    text_w_handle, text_h_approx_handle = draw.textsize(handle_text_content, font=font_handle_text)
                    (ascent_handle, descent_handle) = font_handle_text.getmetrics(); text_h_handle = ascent_handle + descent_handle
                pos_x_handle = image_size[0] - text_w_handle - padding_handle_text_x
                pos_y_handle = image_size[1] - text_h_handle - padding_handle_text_y 
                draw.text((pos_x_handle, pos_y_handle), handle_text_content, font=font_handle_text, fill=handle_text_fill_color)
                self.logger.info(f"Texto '{handle_text_content}' (inferior direito, 100% cor) adicionado.")
            except Exception as e_handle_text:
                self.logger.error(f"Erro ao criar texto do handle: {e_handle_text}", exc_info=True)

            # --- CONFIGURAÇÕES DA SOMBRA PARA O TEXTO PRINCIPAL ---
            shadow_offset = (2, 2) # Deslocamento da sombra (x, y) - AJUSTADO PARA (2,2)
            shadow_color_rgb = (0, 0, 0) # Cor da sombra (preto)
            
            # Fontes e tamanhos para o conteúdo principal
            font_title = self.fonts.get('title') or self.fonts.get('default_body') or ImageFont.load_default()
            font_body = self.fonts.get('body') or self.fonts.get('default_body') or ImageFont.load_default()
            font_author = self.fonts.get('author') or self.fonts.get('default_body') or ImageFont.load_default()
            
            font_title_size = 70; font_body_size = 50; font_author_size = 35
            font_title = font_title.font_variant(size=font_title_size)
            font_body = font_body.font_variant(size=font_body_size)
            font_author = font_author.font_variant(size=font_author_size)

            padding = 80
            max_text_width_pixels = image_size[0] - 2 * padding
            
            # Cálculo da altura total e centralização vertical (como antes)
            total_content_height = 0; temp_title_lines = []; temp_body_lines = []; temp_author_lines = []
            title_text = elements.get("title_text"); main_text = elements.get("main_text", ""); author_text = elements.get("author_text")
            line_height_title = font_title_size * 1.2; spacing_after_title = font_title_size * 0.5
            line_height_body = font_body_size * 1.3; spacing_before_author = font_body_size * 0.3
            line_height_author = font_author_size * 1.2
            if title_text:
                temp_title_lines = wrap(title_text, width=int(max_text_width_pixels / (font_title_size * 0.55)))
                total_content_height += len(temp_title_lines) * line_height_title
                total_content_height += spacing_after_title
            if main_text:
                raw_body_lines = main_text.split('\n')
                for raw_line_idx, line_candidate in enumerate(raw_body_lines):
                    wrapped_lines = wrap(line_candidate, width=int(max_text_width_pixels / (font_body_size * 0.5)))
                    temp_body_lines.extend(wrapped_lines)
                    if wrapped_lines: 
                        total_content_height += (len(wrapped_lines) -1) * line_height_body + font_body_size
                        if raw_line_idx < len(raw_body_lines) -1 : total_content_height += (line_height_body - font_body_size) 
            if author_text:
                if main_text or title_text : total_content_height += spacing_before_author
                temp_author_lines = wrap(f"— {author_text}", width=int(max_text_width_pixels / (font_author_size * 0.5)))
                total_content_height += len(temp_author_lines) * line_height_author
            if temp_title_lines and not temp_body_lines and not temp_author_lines: total_content_height -= (line_height_title - font_title_size)
            elif temp_body_lines and not temp_author_lines : total_content_height -= (line_height_body - font_body_size)
            elif temp_author_lines: total_content_height -= (line_height_author - font_author_size)
            current_y = (image_size[1] - total_content_height) / 2

            # Desenhar conteúdo principal com sombra
            if title_text:
                for line_idx, line in enumerate(temp_title_lines):
                    line_bbox = draw.textbbox((0,0), line, font=font_title); line_width = line_bbox[2] - line_bbox[0]
                    text_x = (image_size[0] - line_width) / 2
                    # Desenhar sombra
                    draw.text((text_x + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_title, fill=shadow_color_rgb)
                    # Desenhar texto principal
                    draw.text((text_x, current_y), line, font=font_title, fill=text_color)
                    current_y += line_height_title 
                current_y += spacing_after_title
            
            if main_text:
                body_lines_to_draw = temp_body_lines 
                for line_idx, line in enumerate(body_lines_to_draw):
                    line_bbox = draw.textbbox((0,0), line, font=font_body); line_width = line_bbox[2] - line_bbox[0]
                    text_x = (image_size[0] - line_width) / 2
                    # Desenhar sombra
                    draw.text((text_x + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_body, fill=shadow_color_rgb)
                    # Desenhar texto principal
                    draw.text((text_x, current_y), line, font=font_body, fill=text_color)
                    current_y += line_height_body if line_idx < len(body_lines_to_draw) - 1 else font_body_size
            
            if author_text:
                if main_text or title_text: current_y += spacing_before_author
                author_lines_to_draw = temp_author_lines
                for line_idx, line in enumerate(author_lines_to_draw):
                    line_bbox = draw.textbbox((0,0), line, font=font_author); line_width = line_bbox[2] - line_bbox[0]
                    text_x_author = image_size[0] - line_width - padding # Alinhado à direita
                    # Desenhar sombra
                    draw.text((text_x_author + shadow_offset[0], current_y + shadow_offset[1]), line, font=font_author, fill=shadow_color_rgb)
                    # Desenhar texto principal
                    draw.text((text_x_author, current_y), line, font=font_author, fill=text_color)
                    current_y += line_height_author if line_idx < len(author_lines_to_draw) -1 else font_author_size
            
            small_logo_path = self.templates_dir / "logo" / "logo.png" 
            if small_logo_path.exists() and small_logo_path != self.watermark_logo_image_path : 
                try:
                    logo_img_small = Image.open(small_logo_path).convert("RGBA")
                    logo_width_small = 150 
                    logo_ratio_small = logo_width_small / logo_img_small.width
                    logo_height_small = int(logo_img_small.height * logo_ratio_small)
                    logo_img_small = logo_img_small.resize((logo_width_small, logo_height_small), Image.Resampling.LANCZOS)
                    logo_x_small = image_size[0] - logo_width_small - padding // 2
                    logo_y_small = image_size[1] - logo_height_small - padding // 2
                    img.paste(logo_img_small, (logo_x_small, logo_y_small), logo_img_small)
                except Exception as e_logo_small:
                    self.logger.warning(f"Não foi possível adicionar o logo pequeno no canto: {e_logo_small}")


            output_path = self.output_dir / f"{content_id}.png"
            img.save(output_path)
            self.logger.info(f"Imagem salva em {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Erro ao gerar imagem com Pillow: {e}", exc_info=True)
            return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    script_dir = Path(__file__).parent
    project_root_for_test = script_dir.parent.parent

    (project_root_for_test / "assets/templates/fonts").mkdir(parents=True, exist_ok=True)
    (project_root_for_test / "assets/templates/backgrounds").mkdir(parents=True, exist_ok=True)
    (project_root_for_test / "assets/templates/logo").mkdir(parents=True, exist_ok=True)
    (project_root_for_test / "output/images").mkdir(parents=True, exist_ok=True)
    (project_root_for_test / "config").mkdir(parents=True, exist_ok=True)

    knowledge_base_real_path = project_root_for_test / "config" / "knowledge_base.yaml"

    if not knowledge_base_real_path.exists():
        logging.error(f"ERRO CRÍTICO: O arquivo principal knowledge_base.yaml NÃO foi encontrado em {knowledge_base_real_path}")
        # sys.exit(1) # Descomente para parar
    
    dummy_bg_path = project_root_for_test / "assets/templates/backgrounds/dummy_bg.png"
    if not dummy_bg_path.exists() and PIL_AVAILABLE:
        try:
            bg_img = Image.new('RGB', (1080, 1080), color = (200, 210, 220))
            bg_img.save(dummy_bg_path); logging.info(f"Background dummy criado em {dummy_bg_path}")
        except Exception as e: logging.error(f"Erro ao criar background dummy: {e}")

    dummy_logo_path = project_root_for_test / "assets/templates/logo/logo.png"
    if not dummy_logo_path.exists() and PIL_AVAILABLE:
        try:
            logo_img = Image.new('RGBA', (300, 100), color = (0,0,0,0)) 
            d_logo = ImageDraw.Draw(logo_img)
            try: font_logo = ImageFont.truetype("Montserrat-Regular.ttf", 60)
            except IOError:
                try: font_logo = ImageFont.truetype("arial.ttf", 60)
                except IOError: font_logo = ImageFont.load_default()
            d_logo.text((10,10), "Logo", fill=(50,50,50,200), font=font_logo) 
            logo_img.save(dummy_logo_path); logging.info(f"Logo dummy criado em {dummy_logo_path}")
        except Exception as e: logging.error(f"Erro ao criar logo dummy: {e}")

    import sys
    if str(project_root_for_test) not in sys.path:
        sys.path.insert(0, str(project_root_for_test))

    creator = CreatorAgent(
        templates_dir=str(project_root_for_test / "assets/templates"),
        output_dir=str(project_root_for_test / "output/images"),
        knowledge_base_path=str(knowledge_base_real_path)
    )
    
    logging.info("--- Testando Geração de Conteúdo (Citação) ---") # AJUSTADO PARA GERAR APENAS UM
    novo_conteudo = creator.create_content(content_type_filter=ContentType.QUOTE) # Gera uma citação
    if novo_conteudo:
        print(f"Conteúdo Gerado: ID={novo_conteudo.id}, Imagem={novo_conteudo.image_path}")
        print(f"Legenda: {novo_conteudo.caption}\\n")
    else:
        print("Falha ao gerar conteúdo (verifique knowledge_base.yaml e se há citações).\\n")
    
    # REMOVIDA A SEGUNDA CHAMADA PARA GERAR CONCEITO
    # logging.info("--- Testando Geração de Conceito ---")
    # novo_conteudo_conceito = creator.create_content(content_type_filter=ContentType.CONCEPT)
    # if novo_conteudo_conceito:
    #     print(f"Conteúdo (Conceito) Gerado: ID={novo_conteudo_conceito.id}, Imagem={novo_conteudo_conceito.image_path}")
    #     print(f"Legenda: {novo_conteudo_conceito.caption}\\n")
    # else:
    #     print("Falha ao gerar conteúdo de conceito (verifique o knowledge_base.yaml).\\n")
    
    print("Verifique a pasta output/images pela imagem gerada.")
    if not knowledge_base_real_path.exists():
         print(f"ATENÇÃO: O ARQUIVO {knowledge_base_real_path} NÃO FOI ENCONTRADO.")
