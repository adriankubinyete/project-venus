import hashlib

def sha1(keyword:str):
    return str(hashlib.sha1(f"{keyword}".encode('utf-8')).hexdigest())

def ler_arquivo(path:str, encrypt_sha1:bool=False):
    if encrypt_sha1:
        with open(path, 'r') as f:
            return str(sha1(f.readline()))
    else:
        with open(path, 'r') as f:
            return str(f.readline())