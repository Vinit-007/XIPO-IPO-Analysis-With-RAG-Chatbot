import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "XIPO - Explainable IPOs"
    VERSION = "1.0.0"
    
    # Cerebras API Configuration
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "csk-e8der3hkvt6hn2w6efr48d6wx6w9d98tey4t49n5jvvx3wtp")

SETTINGS = Settings()
