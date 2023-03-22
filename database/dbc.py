import mysql.connector as mysql
import hashlib

def sha1(keyword:str):
    return str(hashlib.sha1(f"{keyword}".encode('utf-8')).hexdigest())

def senha_venus():
    with open('secret/senha_venus.txt', 'r') as f:
        return sha1(f.readline())

def db_connect(host:str, user:str, password:str):
    venus_db = mysql.connect(
        host=host,
        user=user,
        password=password
    )
    print(venus_db)

db_connect(
    "192.168.139.134", 
    "projectvenus", 
    senha_venus()
)


#pip install mysql.connector