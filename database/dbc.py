from utilidade.venutils import sha1, lerArquivo, venLog
import mysql.connector as mysql


log = venLog()

class VenusDB:
    def __init__(self,  db_host:str, db_user:str, db_pass:str, db_database:str):
        self.db_host=db_host
        self.db_user=db_user
        self.db_pass=db_pass
        self.db_database=db_database
        log.debug(f"Conectando ao database... ('{self.db_database}' on {self.db_host}, '{self.db_user}'/'{self.db_pass}')")
        self.sql=mysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass, database=self.db_database)

    def validateLogin(self, username:str, password:str):
        #print(f"validateLogin: user = {username}")
        #print(f"validateLogin: pass = {password}")
        c = self.sql.cursor()
        log.debug(f"Consultando token do usuário '{username}'")
        c.execute(f"SELECT token FROM users WHERE username = '{username}' AND password = '{password}'")
        token = c.fetchone() # Seta userId pro que a query retornar
        if(token != None): # Se tiver conteúdo (Query retornou >0 resultados)
            for row in token: 
                token = token[0] # Lê todas as linhas (obrigatório pra limpar o cursor), mas retorna o primeiro valor
            log.debug(f"Token localizado")
            return token
        else: 
            log.error(f"Token não localizado (U: {username}, P: {password})")
            return token # UserID está vazio, esse usuário não existe no DB.
        
    def adminPrivileges(self, token:str):
        c = self.sql.cursor()
        log.debug(f"Consultando privilégios de superuser do token '{token}'")
        c.execute(f"SELECT superuser FROM users WHERE token = '{token}'")
        superuser = c.fetchone()
        if(superuser != None):
            for row in superuser:
                superuser = superuser[0]
            if superuser == 1:
                log.debug(f"T:{token}, SUPERUSER: True")
                return True
            else:
                log.debug(f"T:{token}, SUPERUSER: False")
                return False
        else:
            log.debug(f"T:{token}, SUPERUSER: False")
            return False
        
        # Aumentar/ajustar este item caso adicione novos campos no banco de dados.
    def getSessionInfo(self, token:str):
        c = self.sql.cursor()
        log.debug(f"Obtendo informações para sessão do token '{token}'")
        c.execute(f"SELECT * FROM user_config WHERE token = '{token}'")
        session_tuple = c.fetchall()[0]
        log.debug(f"Sessão obtida: {session_tuple}")
        return {
            "id": session_tuple[0],
            "screen_name": session_tuple[1],
            "email": session_tuple[2],
            "superuser": bool(session_tuple[3]),
            "token": session_tuple[4],
            "organization_id" : session_tuple[5],
        }
        
    def getInstancesForOrg(self, org:list):
        def unpackList(list): 
            ret = ''
            for i in range(0, len(list)):
                # se for o ultimo item, adiciono sem ","
                if i == len(list)-1:
                    ret+=f'{list[i]}'
                # se não for o ultimo item, adiciono com ","
                else:
                    ret+=f'{list[i]}, '
            return ret
        # Transforma list [1, 2, 3, 4] em string "1, 2, 3, 4"
        
        # SELECT id, instance, host, dns FROM organization_info WHERE organization_id IN ()
        c = self.sql.cursor()
        log.debug(f"Obtendo instâncias para a organização '{org}'")
        c.execute(f"SELECT id, instance, host, dns FROM organization_info WHERE organization_id IN ({unpackList(org)})")
        instancias = c.fetchall()
        qt_instancias = len(instancias)
        log.debug(f"Quantidade de resultados: {qt_instancias}")
        log.debug(f"Instâncias obtidas: {instancias}")
        print(instancias)
        return instancias

        
        
        
        



#pip install mysql.connector