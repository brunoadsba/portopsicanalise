import logging
import argparse
import yaml # Para carregar config.yaml
from pathlib import Path

# Importar os Agentes e o modelo Content
from .agents.creator import CreatorAgent
from .agents.poster import PosterAgent
from .agents.supervisor import SupervisorAgent
from .models.content import Content # Pode não ser usado diretamente aqui, mas bom ter à mão

# Idealmente, a configuração de logging viria de um utilitário
# from .utils.logging_config import setup_logging # Assumindo que criaremos este utilitário

def setup_logging(log_config: dict):
    """Configura o logging básico a partir de um dicionário de configuração."""
    level = log_config.get('level', 'INFO').upper()
    log_file = log_config.get('file')
    
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()] # Adiciona output para o console por padrão
    )
    
    if log_file:
        # Adiciona um file handler se um arquivo de log for especificado
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    
    logging.info(f"Logging configurado. Nível: {level}, Arquivo: {log_file if log_file else 'Console'}")


def load_config(config_path_str: str) -> dict:
    """Carrega o arquivo de configuração YAML."""
    config_path = Path(config_path_str)
    if not config_path.is_file():
        logging.error(f"Arquivo de configuração não encontrado: {config_path}")
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
            logging.info(f"Configuração carregada de {config_path}")
            return config
        except yaml.YAMLError as e:
            logging.error(f"Erro ao fazer parse do arquivo de configuração YAML: {e}")
            raise ValueError(f"Erro no formato do arquivo de configuração: {e}")

def main():
    parser = argparse.ArgumentParser(description='Sistema de Agentes para Instagram - Porto Psicanálise')
    parser.add_argument('--config', default='config/config.yaml', 
                        help='Caminho para o arquivo de configuração YAML (relativo à raiz do projeto ou absoluto)')
    parser.add_argument('--mode', choices=['create', 'post', 'supervise', 'full_cycle', 'test_creator'], default='full_cycle',
                        help='Modo de execução: create, post, supervise, full_cycle (todos), test_creator')
    args = parser.parse_args()

    # Determinar o caminho base do projeto para resolver caminhos relativos
    # Isso assume que main.py está em src/ e a raiz do projeto é um nível acima
    project_root = Path(__file__).parent.parent 
    
    # Resolver o caminho do arquivo de configuração
    config_file_path = Path(args.config)
    if not config_file_path.is_absolute():
        config_file_path = project_root / config_file_path

    try:
        config = load_config(str(config_file_path))
    except (FileNotFoundError, ValueError) as e:
        # O logging já foi feito dentro de load_config, mas podemos logar o encerramento.
        logging.critical(f"Encerrando devido a erro na configuração: {e}")
        return

    # Configurar logging a partir do arquivo de configuração
    # Se a chave 'logging' não existir, setup_logging usará padrões.
    setup_logging(config.get('logging', {}))
    
    logging.info(f"Iniciando sistema em modo: {args.mode}")
    
    # Resolver caminhos para os agentes a partir da raiz do projeto e da configuração
    # Garantir que os caminhos sejam passados como strings para os construtores dos agentes
    creator_cfg = config.get('creator', {})
    templates_dir_path = project_root / creator_cfg.get('templates_dir', 'assets/templates')
    output_dir_path = project_root / creator_cfg.get('output_dir', 'output/images')
    kb_path = project_root / creator_cfg.get('knowledge_base', 'config/knowledge_base.yaml') # Ajustado de 'data/' para 'config/'
    
    instagram_cfg = config.get('instagram', {})
    session_file_path = project_root / instagram_cfg.get('session_file', 'data/session.json') # 'data/' pode precisar ser criado

    supervisor_cfg = config.get('supervisor', {})
    metrics_path = project_root / supervisor_cfg.get('metrics', {}).get('store_path', 'data/metrics.db')


    try:
        # Inicializar agentes com base na configuração
        creator = CreatorAgent(
            templates_dir=str(templates_dir_path),
            output_dir=str(output_dir_path),
            knowledge_base_path=str(kb_path)
            # Adicionar outros parâmetros de creator_cfg se necessário (use_ai_generation, api_key, etc.)
        )
        
        poster = PosterAgent(
            username=instagram_cfg.get('username'), # Idealmente de env var
            password=instagram_cfg.get('password'), # Idealmente de env var
            session_file=str(session_file_path)
        )
        
        supervisor = SupervisorAgent(
            notification_email=supervisor_cfg.get('notifications', {}).get('email'),
            # Adicionar outros parâmetros de notifications (webhook, telegram)
            metrics_store_path=str(metrics_path)
        )
        
        # Lógica de execução baseada no modo
        content_to_post: Optional[Content] = None

        if args.mode in ['create', 'full_cycle', 'test_creator']:
            logging.info("Executando Agente Criador...")
            content_to_post = creator.create_content() # Categoria e tipo podem ser passados aqui
            if content_to_post:
                logging.info(f"Conteúdo criado: {content_to_post.id} - {content_to_post.title}")
                if content_to_post.image_path:
                     logging.info(f"Imagem gerada em: {content_to_post.image_path}")
                else:
                    logging.warning(f"Nenhuma imagem foi gerada para o conteúdo: {content_to_post.id}")
            else:
                logging.error("Agente Criador não produziu conteúdo.")

        if args.mode in ['post', 'full_cycle']:
            if content_to_post:
                if content_to_post.image_path: # Só posta se tiver imagem
                    logging.info("Executando Agente Postador...")
                    post_id = poster.post_content(content_to_post)
                    if post_id:
                        content_to_post.posted = True
                        content_to_post.post_id = post_id
                        logging.info(f"Conteúdo postado. Post ID: {post_id}")
                    else:
                        logging.error("Falha ao postar conteúdo.")
                else:
                    logging.warning(f"Conteúdo {content_to_post.id} não possui imagem, pulando postagem.")
            else:
                logging.warning("Nenhum conteúdo disponível para postar (modo 'post' ou 'full_cycle' sem conteúdo prévio).")
        
        if args.mode in ['supervise', 'full_cycle']:
            # Lógica de supervisão - pode ser agendada ou disparada após postagem
            # Para este esqueleto, vamos simular uma verificação se um post_id existe
            if content_to_post and content_to_post.post_id:
                logging.info(f"Executando Agente Supervisor para o post ID: {content_to_post.post_id}...")
                if supervisor.verify_post(content_to_post.post_id):
                    logging.info(f"Verificação da postagem {content_to_post.post_id} bem-sucedida.")
                    metrics = supervisor.collect_engagement_metrics(content_to_post.post_id)
                    if metrics:
                        logging.info(f"Métricas coletadas para {content_to_post.post_id}: {metrics}")
                else:
                    logging.error(f"Falha na verificação da postagem {content_to_post.post_id}.")
            else:
                logging.info("Nenhum post ID recente para supervisionar ou modo 'supervise' sem postagem prévia.")
            
            # Health check geral
            if supervisor.health_check():
                logging.info("Health check do sistema: OK")
            else:
                logging.warning("Health check do sistema: FALHOU")


    except Exception as e:
        logging.error(f"Erro fatal no fluxo principal do sistema: {e}", exc_info=True)
        # Enviar alerta crítico aqui se configurado
        # if 'supervisor' in locals() and supervisor:
        # supervisor._send_alert(f"Erro fatal no sistema: {e}", level="CRITICAL")
        
    logging.info("Processo principal concluído.")

if __name__ == "__main__":
    # O logging é configurado dentro do main() após carregar config.
    # Para logs antes disso (ex: erro ao carregar config), um basicConfig pode ser útil aqui,
    # mas pode ser sobrescrito.
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
