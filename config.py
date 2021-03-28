import os
from pathlib import Path

from dotenv import load_dotenv


basedir = Path(__file__).resolve().parent
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """
    Set base Flask configuration vars.
    """
    # General Config
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_URL'),
    }
    # Default number of documents on page (api results pagination)
    DEFAULT_PAGINATION_LIMIT = 6
    MAX_PAGINATION_LIMIT = 30

