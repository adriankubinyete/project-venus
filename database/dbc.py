from utilidade.venutils import sha1, lerArquivo, venLog
import mysql.connector as mysql


log = venLog()

class VenusDB:
    def __init__(self,  db_host:str, db_user:str, db_pass:str, db_database:str):
        self.db_host=db_host
        self.db_user=db_user
        self.db_pass=db_pass
        self.db_database=db_database
        log.debug(f"Conectando ao database... ({self.db_host}, {self.db_user}/{self.db_pass})")
        self.sql=mysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass, database=self.db_database)

    def validateLogin(self, username:str, password:str):
        print(f"validateLogin: user = {username}")
        print(f"validateLogin: pass = {password}")
        c = self.sql.cursor()
        c.execute(f"SELECT id FROM users WHERE username = '{username}' AND password = '{password}'")
        userId = c.fetchone() # Seta userId pro que a query retornar
        if(userId != None): # Se tiver conteúdo (Query retornou >0 resultados)
            for row in userId: 
                userId = userId[0] # Lê todas as linhas (obrigatório pra limpar o cursor), mas retorna o primeiro valor
            return userId
        else: 
            return userId # UserID está vazio, esse usuário não existe no DB.
        
        
        



#pip install mysql.connector