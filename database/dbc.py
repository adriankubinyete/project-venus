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
        
    def getInstancesForOrg(self, org:list, admin:bool=False):
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
        if admin:
            c.execute(f"SELECT id, instance, host, dns FROM organization_info")
        else:
            c.execute(f"SELECT id, instance, host, dns FROM organization_info WHERE organization_id IN ({unpackList(org)})")
        instancias = c.fetchall()
        qt_instancias = len(instancias)
        log.debug(f"Quantidade de resultados: {qt_instancias}")
        log.debug(f"Instâncias obtidas: {instancias}")
        return instancias

        
        
        
        



#pip install mysql.connector