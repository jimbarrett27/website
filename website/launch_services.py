from waitress import serve
from app import app
import logging
import os

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S' 
)

port = os.environ.get('PORT')
serve(app, port=port)
