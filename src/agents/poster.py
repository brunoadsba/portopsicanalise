import logging
import time
from typing import Optional
from pathlib import Path # Importado para usar Path
# Importar o cliente da API do Instagram (instagrapi)
try:
    from instagrapi import Client
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False
    # Loggar a ausência do instagrapi no __init__ se necessário

# Importar o modelo Content
from ..models.content import Content

class PosterAgent:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 session_file: Optional[str] = None):
        self.username = username
        self.password = password # Idealmente, carregar de variáveis de ambiente
        self.session_file = session_file # Para persistir a sessão do Instagram

        # Cliente da API do Instagram (ex: instagrapi) será inicializado aqui
        self.instagram_client: Optional[Client] = None # Especificar tipo opcional de Client

        # Configurações básicas de logging para o agente
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            noisy_logs_filter = type('NoisyLogsFilter', (logging.Filter,), {'filter': lambda self, record: not any(msg in record.getMessage() for msg in ['login_by_pk', 'password_url', 'logged_in_user', 'Returning cached result', 'GET request:'])})() # Adicionado filtro para GET requests também
            self.logger.addFilter(noisy_logs_filter)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info("PosterAgent inicializado.")
        if not INSTAGRAPI_AVAILABLE:
             self.logger.error("A biblioteca 'instagrapi' não está instalada. A funcionalidade de postagem real será desabilitada.")
        else:
            self._initialize_client()

    def _initialize_client(self) -> bool:
        """
        Inicializa o cliente da API do Instagram usando instagrapi.
        Tenta carregar a sessão se session_file for fornecido.
        Caso contrário, tenta fazer login com username/password.
        """
        if not INSTAGRAPI_AVAILABLE:
            self.logger.error("instagrapi não está disponível para inicializar o cliente.")
            return False

        self.instagram_client = Client()
        self.instagram_client.delay_range = [1, 3] # Ajuste o delay conforme necessário
        try:
            if self.session_file and Path(self.session_file).exists():
                self.logger.info(f"Tentando carregar sessão do Instagram de {self.session_file}")
                self.instagram_client.load_settings(self.session_file)
                # Validar sessão carregada tentando fazer algo simples ou relogando
                try:
                     self.instagram_client.get_self_info() # Tenta uma chamada simples para validar
                     self.logger.info("Sessão do Instagram carregada e validada.")
                except Exception:
                     self.logger.warning("Sessão carregada parece inválida ou expirada. Tentando relogar...")
                     if not self.instagram_client.login(self.username, self.password):
                         self.logger.error("Falha ao relogar com a sessão existente. Verifique credenciais.")
                         self.instagram_client = None
                         return False
                     self.logger.info("Relogin com sessão existente bem-sucedido.")

            elif self.username and self.password:
                self.logger.info("Credenciais fornecidas. Tentando fazer login no Instagram.")
                if not self.instagram_client.login(self.username, self.password):
                    self.logger.error("Falha ao fazer login no Instagram com as credenciais fornecidas.")
                    self.instagram_client = None
                    return False

                self.logger.info("Login no Instagram realizado.")
                if self.session_file: # Salvar a nova sessão se o caminho for fornecido
                    try:
                        self.instagram_client.dump_settings(self.session_file)
                        self.logger.info(f"Nova sessão salva em {self.session_file}")
                    except Exception as e_dump:
                        self.logger.warning(f"Não foi possível salvar o arquivo de sessão em {self.session_file}: {e_dump}")

            else:
                self.logger.warning("Credenciais (username/password) ou arquivo de sessão não fornecidos. Cliente Instagram não logado para postagem real.")
                self.instagram_client = None # Garantir que o cliente não seja usado para postagem real
                return False # Não foi possível inicializar para postagem real

        except Exception as e:
            self.logger.error(f"Erro crítico ao inicializar cliente do Instagram: {e}", exc_info=True)
            self.instagram_client = None # Garante que o cliente não seja usado se a inicialização falhar
            return False
        return True # Inicialização bem-sucedida para postagem real

    def post_content(self, content: Content) -> Optional[str]:
        """
        Posta o conteúdo fornecido no Instagram usando instagrapi.
        Retorna o ID da postagem se bem-sucedido, None caso contrário.
        """
        self.logger.info(f"Solicitação para postar conteúdo: {content.id} - {content.title}")

        if not INSTAGRAPI_AVAILABLE or not self.instagram_client:
            self.logger.error("Cliente Instagram não inicializado (instagrapi ausente ou login falhou). Não é possível postar realmente.")
            # Simular postagem em modo de falha de inicialização
            simulated_post_id = f"simulated_failure_{int(time.time())}"
            self.logger.info(f"Conteúdo {content.id} 'simulado' como falha de postagem com ID: {simulated_post_id}")
            return simulated_post_id # Retorna ID simulado mesmo na falha para teste

        if not content.image_path or not Path(content.image_path).exists():
            self.logger.error(f"Caminho da imagem inválido ou arquivo não encontrado para o conteúdo {content.id}: {content.image_path}. Não é possível postar.")
            return None # Falha real se a imagem não existe

        # Lógica para postar a imagem e legenda no Instagram usando instagrapi
        try:
            self.logger.info(f"Realizando postagem da imagem '{content.image_path}' com legenda.")
            media = self.instagram_client.photo_upload(
                path=str(content.image_path), # instagrapi espera string ou Path
                caption=content.caption
            )
            self.logger.info(f"Conteúdo {content.id} postado com sucesso. Post ID: {media.id}")
            return str(media.id) # Retorna o ID real da postagem
        except Exception as e:
            self.logger.error(f"Erro REAL ao postar conteúdo {content.id} no Instagram: {e}", exc_info=True)
            return None # Falha real na postagem

    # Outros métodos como agendamento, verificação de status, etc., podem ser adicionados.

if __name__ == '__main__':
    # Exemplo de uso para teste
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # --- Criação de Dummy Image para o teste do PosterAgent ---
    # Usar um caminho temporário mais robusto, talvez dentro de output/images
    poster_test_output_dir = Path("output/images")
    poster_test_output_dir.mkdir(parents=True, exist_ok=True)
    # Gerar um nome de arquivo único para a imagem dummy do teste
    dummy_image_filename = f"dummy_poster_test_image_{int(time.time())}.png"
    dummy_image_path = poster_test_output_dir / dummy_image_filename # Definir o caminho completo aqui

    PIL_AVAILABLE_FOR_POSTER_TEST = False
    try:
        from PIL import Image, ImageDraw, ImageFont
        PIL_AVAILABLE_FOR_POSTER_TEST = True
    except ImportError:
        logging.error("Pillow não instalado. Não foi possível criar a imagem dummy para teste do PosterAgent. Postagem real falhará.")


    if PIL_AVAILABLE_FOR_POSTER_TEST:
        try:
            img = Image.new('RGB', (600, 600), color = (150, 200, 250))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except IOError:
                font = ImageFont.load_default()
            draw.text((50, 250), "Imagem de Teste\n(PosterAgent)", fill=(50,50,50), font=font)
            img.save(dummy_image_path)
            logging.info(f"Imagem dummy para teste do PosterAgent criada em: {dummy_image_path}")
        except Exception as e:
            logging.error(f"Erro ao criar imagem dummy para teste do PosterAgent: {e}")
            # Se a criação falhar, dummy_image_path ainda terá o caminho,
            # mas o arquivo não existirá, o que será tratado no post_content.


    # Criar um objeto Content dummy para teste do PosterAgent
    from datetime import datetime
    try:
        from ..models.content import ContentCategory, ContentType
        Content = Content # Usar a classe real se o import funcionar
        ContentCategory = ContentCategory
        ContentType = ContentType
    except ImportError as e:
         logging.error(f"ImportError para Content/Enums no teste do PosterAgent: {e}. Usando dummies.")
         ContentCategory = type('ContentCategory', (object,), {'REFLECTION': 'reflection'}) # Dummy com valor
         ContentType = type('ContentType', (object,), {'CONCEPT': 'concept'}) # Dummy com valor
         # Dummy Content que apenas aceita os args
         Content = type('Content', (object,), {'__init__': lambda self, **kwargs: self.__dict__.update(kwargs), '__repr__': lambda self: str(self.__dict__)})


    dummy_content = Content(
        id=f"dummy_poster_test_{int(time.time())}", # ID temporário para o teste
        title="Teste de Postagem",
        text="Este é um texto de teste para a imagem.",
        caption="Esta é uma legenda de teste para o Instagram, com algumas #hashtags #TestePoster #API.",
        category=ContentCategory.REFLECTION,
        content_type=ContentType.CONCEPT,
        hashtags=["TestePoster", "API"],
        # Passar o caminho da imagem dummy para o objeto content
        image_path=str(dummy_image_path), # Sempre passe o caminho gerado
        created_at=datetime.now()
    )

    # Configurações para carregar credenciais de .env
    instagram_username = None
    instagram_password = None
    session_file_path = Path("temp_poster_session.json")

    try:
        import os
        from dotenv import load_dotenv
        # Assumindo que o .env está na raiz do projeto (um nível acima de src)
        dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(dotenv_path=dotenv_path)
        instagram_username = os.getenv("INSTAGRAM_USERNAME")
        instagram_password = os.getenv("INSTAGRAM_PASSWORD")
        if instagram_username and instagram_password:
             logging.info("Variáveis de ambiente (Instagram) carregadas com sucesso.")
        else:
             # Não trate como erro crítico aqui, pois o PosterAgent vai lidar com a falta de credenciais
             logging.warning("Variáveis de ambiente (INSTAGRAM_USERNAME/INSTAGRAM_PASSWORD) não encontradas ou incompletas no .env.")

    except ImportError:
        logging.warning("A biblioteca 'python-dotenv' não está instalada. Credenciais de ambiente não serão carregadas.")
    except Exception as e:
        logging.error(f"Erro ao carregar variáveis de ambiente: {e}")


    # Inicializar PosterAgent com credenciais carregadas do .env
    # Esta linha AGORA tenta o login REAL se as credenciais forem encontradas
    # Se as credenciais não forem encontradas, instagram_client será None e a postagem será simulada.
    poster = PosterAgent(username=instagram_username, password=instagram_password, session_file=str(session_file_path))

    print("\n--- Executando teste de postagem ---")
    # A postagem AGORA tentará usar o cliente instagrapi real, se inicializado.
    # Se a imagem dummy não foi criada (Pillow ausente ou erro), ou se o login falhou, post_content retornará None ou um ID simulado.
    post_id = poster.post_content(dummy_content)

    if post_id:
        logging.info(f"Resultado da postagem (simulado ou real): ID={post_id}. Verifique os logs acima para detalhes.")
        # Se o ID não começar com "simulated", significa que tentou a postagem real
        if not str(post_id).startswith("simulated_failure_") and not str(post_id).startswith("simulated_"):
            print(f"\nPOSSÍVEL POSTAGEM REAL NO INSTAGRAM COM ID: {post_id}")
            print("Verifique a conta de Instagram de teste!")
    else:
        # Este caso ocorre se post_content retornou None (erro real, como imagem não encontrada)
        logging.error("Falha na postagem REAL. Verifique os logs para erros específicos (ex: imagem não encontrada).")

    # Limpar arquivo de sessão dummy e imagem dummy após o teste
    # Manter a limpeza da sessão em qualquer caso de execução do teste
    if session_file_path.exists():
        try:
             session_file_path.unlink()
             logging.info(f"Arquivo de sessão dummy '{session_file_path}' removido.")
        except Exception as e:
             logging.warning(f"Não foi possível remover o arquivo de sessão dummy '{session_file_path}': {e}")

    # Limpar a imagem dummy SOMENTE se ela foi criada com sucesso E existir
    if dummy_image_path and dummy_image_path.exists():
        try:
            dummy_image_path.unlink()
            logging.info(f"Imagem dummy '{dummy_image_path}' removida.")
            # Opcional: remover o diretório output/images se ficar vazio (cuidado em produção)
            # if poster_test_output_dir.exists() and not any(poster_test_output_dir.iterdir()):
            #      try: poster_test_output_dir.rmdir()
            #      except OSError: pass # Ignorar se não estiver vazio

        except Exception as e:
             logging.warning(f"Não foi possível remover a imagem dummy '{dummy_image_path}': {e}")
    elif dummy_image_path:
         logging.warning(f"Imagem dummy '{dummy_image_path}' não existia para ser removida.")


    print("\nTeste de postagem concluído.")
