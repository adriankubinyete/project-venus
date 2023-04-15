from utilidade.venutils import sha1, lerArquivo, venLog
import mysql.connector as mysql

log = venLog()

class VenusDB:
    def __init__(self,  db_host:str, db_user:str, db_pass:str, db_database:str, create_db:bool=False):
        self.db_host=db_host
        self.db_user=db_user
        self.db_pass=db_pass
        self.db_database=db_database
        self.create_db=create_db

        self.db_usuarios = 'usuarios'
        self.db_usuarios_info = 'info_usuarios'
        self.db_empresas = 'empresas'
        self.db_instancias = 'hosts'
        
        log.debug(f"Conectando ao database... ('{self.db_database}' on {self.db_host}, '{self.db_user}'/'{self.db_pass}')")
        
        if db_database:
            if self.create_db:
                self.sql=mysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass)
            else:
                self.sql=mysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass, database=self.db_database) # Conectado, mas não está
        else:
            raise Exception("Você não passou um banco de dados.")

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
            "instances" : None, # utilizado para display dos cards de host
        }

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
        log.debug(f"Obtendo instâncias para a organização \"{org}\"")
        if admin:
            c.execute(f"SELECT id, name, host, dns FROM instances")
        else:
            c.execute(f"SELECT id, name, host, dns FROM instances WHERE organization_id IN ({unpackList(org)})")
        instancias = c.fetchall()
        qt_instancias = len(instancias)
        log.debug(f"Quantidade de resultados: {qt_instancias}")
        log.debug(f"Lista de instâncias obtidas: {instancias}")
        return instancias

    def beware_this_function_purges_the_database(self):
        log.warning(f"############ DELETANDO BANCO DE DADOS \"{self.db_database}\" ############")
        c = self.sql.cursor()
        query = f"DROP DATABASE IF EXISTS {self.db_database}"
        # drop database
        c.execute(query)
        log.warning(f"############ BANCO DE DADOS \"{self.db_database}\" DELETADO! ############")
        
    def boot_database_configuration(self):
        if self.create_db: # Se for um create-db
            
            # funções de boot, criação
            def cdb_database(): # Criar DB
                c = self.sql.cursor()
                query = f"CREATE DATABASE IF NOT EXISTS {self.db_database} CHARACTER SET utf8mb4"
                c.execute(query)
                query2 = f"USE {self.db_database}"
                c.execute(query2)
                log.debug(f'Criando Database \"{self.db_database}\" > DONE')

            def ctable_empresas(): # Criar Empresas (Grupo de Hosts)
                c = self.sql.cursor()
                query = f"""CREATE TABLE IF NOT EXISTS {self.db_empresas} (
        id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
        name VARCHAR(255) NOT NULL
        );"""
                c.execute(query)
                log.debug(f'Criando Table \"{self.db_empresas}\" > DONE')

            def ctable_usuarios(): # Criar Usuários
                c = self.sql.cursor()
                query = f"""CREATE TABLE IF NOT EXISTS {self.db_usuarios} (
        id INT AUTO_INCREMENT NOT NULL,
        username VARCHAR(255) NOT NULL,
        superuser INT DEFAULT 0,
        password VARCHAR(255) NOT NULL,
        token VARCHAR(255) UNIQUE NOT NULL,
        CONSTRAINT PRIMARY KEY (id)
        );"""
                c.execute(query)
                log.debug(f'Criando Table \"{self.db_usuarios}\" > DONE')

            def ctable_conf_usuarios(): # Criar Informações de Usuários
                c = self.sql.cursor()
                query = f"""CREATE TABLE IF NOT EXISTS {self.db_usuarios_info} (
        id INT AUTO_INCREMENT NOT NULL,
        screen_name VARCHAR(255),
        email VARCHAR(255) NULL,
        superuser INT DEFAULT 0,
        token VARCHAR(255) UNIQUE NOT NULL,
        organization_id INT NULL,
        CONSTRAINT PRIMARY KEY (id),
        CONSTRAINT FOREIGN KEY (organization_id) REFERENCES {self.db_empresas}(id),
        CONSTRAINT FOREIGN KEY (token) REFERENCES {self.db_usuarios}(token)
        );"""
                c.execute(query)
                log.debug(f'Criando Table \"{self.db_usuarios_info}\" > DONE')

            def ctable_instancias(): # Criar Instâncias (Hosts)
                c = self.sql.cursor()
                query = f"""CREATE TABLE IF NOT EXISTS {self.db_instancias} (
        id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
        organization_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        host VARCHAR(255) NULL,
        dns VARCHAR(255) NULL,
        ssh_port INT NULL,
        ssh_user VARCHAR(255) NOT NULL,
        ssh_password VARCHAR(255) NULL,
        ssh_privatekey VARCHAR(255) NULL,
        CONSTRAINT FOREIGN KEY (organization_id) REFERENCES {self.db_empresas}(id)
        );"""
                c.execute(query)
                log.debug(f'Criando Table \"{self.db_instancias}\" > DONE')
            
            # Configurando.
            log.debug(f'Criando Database \"{self.db_database}\"')
            cdb_database()
            
            log.debug(f'Criando Table \"{self.db_empresas}\"')
            ctable_empresas()
            
            log.debug(f'Criando Table \"{self.db_usuarios}\"')
            ctable_usuarios()
            
            log.debug(f'Criando Table \"{self.db_usuarios_info}\"')
            ctable_conf_usuarios()
            
            log.debug(f'Criando Table \"{self.db_instancias}\"')
            ctable_instancias()
        else: # Se não for um create_db
            log.debug(f"Tentou utilizar a sequência de criação de banco de dados para \"{self.db_database}\", porém \"create_db=False\", logo, não foi dado sequência na função.")
        
    def bulk_insert(self):
        log.debug(f"Iniciando BULK INSERT")
        c = self.sql.cursor()
        query = lerArquivo("secret/venus_mariadb_bulkinsert.txt", entire_file=True)
        #welp, o que estiver em bulkinsert deve estar coerente com o formato (nomes de tabelas, etc) do banco de dados, não há contorno pra isso... (que eu saiba)
        c.execute(query, multi=True)
        
def dev():
    raise Exception("não rode o script do banco de dados diretamente!! >:(")

if __name__ == "__main__":
    dev()

#pip install mysql.connector