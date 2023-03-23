from datetime import datetime
import hashlib
import logging


def sha1(keyword:str):
    return str(hashlib.sha1(f"{keyword}".encode('utf-8')).hexdigest())

def lerArquivo(path:str, encrypt_sha1:bool=False):
    if encrypt_sha1:
        with open(path, 'r') as f:
            return str(sha1(f.readline()))
    else:
        with open(path, 'r') as f:
            return str(f.readline())
        
def venLog():
    LOG_FILE = f"logfile-{datetime.now().strftime('%d-%m-%y')}.log"
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.DEBUG,
        format='[%(asctime)s] <%(levelname)s> : %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    return logging.getLogger(__name__)