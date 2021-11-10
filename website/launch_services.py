from waitress import serve
from app import app
import logging
import os
from bots.hello_bot import launch_hello_bot



logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S' 
)

# launch_hello_bot()

port = os.environ.get('PORT')
serve(app, port=port)
