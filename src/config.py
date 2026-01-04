import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv('MODEL_NAME', '')
PLATFORM = os.getenv('PLATFORM', 'openai')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', '')
SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY', '')
SILICONFLOW_BASE_URL = os.getenv('SILICONFLOW_BASE_URL', '')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', '')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

INPUT_COST_PER_M_TOKENS = float(os.getenv('INPUT_COST_PER_M_TOKENS', '2.0'))
OUTPUT_COST_PER_M_TOKENS = float(os.getenv('OUTPUT_COST_PER_M_TOKENS', '8.0'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PDFS_DIR = os.path.join(DATA_DIR, 'pdfs')
INTERMEDIATE_DIR = os.path.join(DATA_DIR, 'intermediate')
REFINED_DIR = os.path.join(DATA_DIR, 'refined')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
AGENT_LOGS_DIR = os.path.join(LOGS_DIR, 'agents')
GLOBAL_LOGS_DIR = os.path.join(LOGS_DIR, 'global')
CHECKPOINT_DIR = os.path.join(INTERMEDIATE_DIR, 'checkpoints')

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PDFS_DIR, exist_ok=True)
os.makedirs(INTERMEDIATE_DIR, exist_ok=True)
os.makedirs(REFINED_DIR, exist_ok=True)
os.makedirs(AGENT_LOGS_DIR, exist_ok=True)
os.makedirs(GLOBAL_LOGS_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

