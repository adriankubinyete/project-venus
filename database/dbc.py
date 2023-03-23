import mysql.connector as mysql
from utilidade.venutils import sha1, ler_arquivo

class VenusDB:
    def __init__(self,  db_host:str, db_user:str, db_pass:str):
        self.db_host=db_host
        self.db_user=db_user
        self.db_pass=db_pass
        self.sql=mysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass)
    
#pip install mysql.connector