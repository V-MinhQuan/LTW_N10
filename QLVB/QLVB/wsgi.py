import os
import sys
from pathlib import Path

# Add project root and QLVB to sys.path so modules like web and settings are discoverable in serverless
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PARENT_DIR = BASE_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
app = application
