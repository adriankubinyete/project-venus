from utilidade.venutils import sha1, lerArquivo, venLog
import mysql.connector as mysql

log = venLog()

class VenusDB:
    def __init__(self,  db_host:str, db_user:str, db_pass:str, db_database:str=False, noselect:bool=False):
        self.db_host=db_host
        self.db_user=db_user
        self.db_pass=db_pass
        self.db_database=db_database

        self.db_usuarios = 'usuarios'
        self.db_usuarios_info = 'info_usuarios'
        self.db_empresas = 'empresas'
        self.db_instancias = 'hosts'
        
        log.debug(f"Conectando ao MYSQL... (DATABASE: '{self.db_database}' | IP: {self.db_host} | USER: '{self.db_user}' | PASS: '{self.db_pass}')")
        
        if noselect:
            log.debug(f"Autenticação sem banco-de-dados definido.")
            print("############ VOCÊ NÃO SELECIONOU UM BANCO DE DADOS. ESQUECEU O NOSELECT ATIVO? ##########")
            self.sql=mysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass)
        else:
            log.debug(f"Autenticação no banco-de-dados {self.db_database}")
            self.sql=mysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass, database=self.db_database)
            
    # Aumentar/ajustar este item caso adicione novos campos no banco de dados.
    def getSessionInfo(self, token:str):
        c = self.sql.cursor(dictionary=True)
        log.debug(f"Obtendo informações para sessão do token '{token}'")
        c.execute(f"SELECT * FROM {self.db_usuarios_info} WHERE token='{token}'")
        session_tuple = c.fetchall()[0]
        log.debug(f"Sessão obtida: {session_tuple}")
        return {
            "id": session_tuple['id'],
            "organization_id": session_tuple['organization_id'],
            "superuser": bool(session_tuple['superuser']),
            "screen_name": session_tuple['screen_name'],
            "email": session_tuple['email'],
            "token" : session_tuple['token'],
            "instances" : None, # utilizado para display dos cards de host
        }

    def validateLogin(self, username:str, password:str):
        #print(f"validateLogin: user = {username}")
        #print(f"validateLogin: pass = {password}")
        c = self.sql.cursor()
        log.debug(f"U: {username} / P: {password} / DB: {self.db_database}: Consultando token do usuário '{username}'")
        c.execute(f"SELECT token FROM {self.db_usuarios} WHERE username='{username}' AND password='{password}'")
        token = c.fetchone() # Seta userId pro que a query retornar
        if(token != None): # Se tiver conteúdo (Query retornou >0 resultados)
            for row in token: 
                token = token[0] # Lê todas as linhas (obrigatório pra limpar o cursor), mas retorna o primeiro valor
            log.debug(f"U: {username} / P: {password} / T: {token} / DB: {self.db_database}: Autenticação bem sucedida: Token localizado.")
            return token
        else: 
            log.error(f"U: {username} / P: {password} / T: {token} / DB: {self.db_database}: Autenticação falhou: Token não localizado.")
            return token # UserID está vazio, esse usuário não existe no DB.
        
    def adminPrivileges(self, token:str):
        c = self.sql.cursor()
        log.debug(f"Consultando privilégios de superuser do token '{token}'")
        c.execute(f"SELECT superuser FROM {self.db_usuarios_info} WHERE token='{token}'")
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
            c.execute(f"SELECT id, name, host, dns FROM {self.db_instancias}")
        else:
            c.execute(f"SELECT id, name, host, dns FROM {self.db_instancias} WHERE organization_id IN ({unpackList(org)})")
        instancias = c.fetchall()
        qt_instancias = len(instancias)
        log.debug(f"Quantidade de resultados: {qt_instancias}")
        log.debug(f"Lista de instâncias obtidas: {instancias}")
        return instancias


    def getInstance(self, instance_id:int):
        c = self.sql.cursor(dictionary=True)
        query = f"SELECT * FROM {self.db_instancias} WHERE id = {instance_id}"
        c.execute(query)
        instance = c.fetchall()[0]
        return {
            "id": instance['id'],
            "organization_id": instance['organization_id'],
            "name": instance['name'],
            "host": instance['host'],
            "dns": instance['dns'],
            "ssh_user": instance['ssh_user'],
            "ssh_port": instance['ssh_port'],
            "ssh_password": instance['ssh_password'],
            "ssh_privatekey": None,
        }

    def updateInstance(self, host_id:int, host_name:str, host_host:str, host_dns:str, host_ssh_port:int, host_ssh_user:str, host_ssh_password:str):
        def fmt_sql(field):
            if field == None:
                return 'NULL'
            elif not field:
                return 'NULL'
            else:
                return f"{field}"

        c = self.sql.cursor()

        c.execute(f"UPDATE {self.db_instancias} SET name = %s, host = %s, dns = %s, ssh_port = %s, ssh_user = %s, ssh_password = %s WHERE id = %s LIMIT 1", (fmt_sql(host_name), fmt_sql(host_host), fmt_sql(host_dns), fmt_sql(host_ssh_port), fmt_sql(host_ssh_user), fmt_sql(host_ssh_password), host_id)) # prevenindo SQL INJECTIONS

        self.sql.commit()







    def purge_database(self):
        log.warning(f"############ DELETANDO BANCO DE DADOS \"{self.db_database}\" ############")
        c = self.sql.cursor()
        query = f"DROP DATABASE IF EXISTS {self.db_database}"
        # drop database
        c.execute(query)
        log.warning(f"############ BANCO DE DADOS \"{self.db_database}\" DELETADO! ############")
        
    def boot_database_configuration(self):
        # funções de boot, criação
        def cdb_database(): # Criar DB
            c = self.sql.cursor()
            query = f"CREATE DATABASE IF NOT EXISTS {self.db_database} CHARACTER SET utf8mb4"
            c.execute(query)
            query2 = f"USE {self.db_database}"
            c.execute(query2)
            self.sql.commit()
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
    organization_id INT NULL,
    superuser INT DEFAULT 0,
    screen_name VARCHAR(255),
    email VARCHAR(255) NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
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
            
        def insert_admin():
            c = self.sql.cursor()
            query = f"""INSERT INTO {self.db_usuarios} (username, password, token) VALUES ('admin', SHA1('admin'), SHA1('admin'));"""
            c.execute(query)
            self.sql.commit()
            log.debug(f'Inserindo ADMIN > DONE')
        
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
        
        #log.debug(f'Inserindo ADMIN')
        #insert_admin()
        
    def bulk_insert(self):
        log.debug(f"Iniciando BULK INSERT")
        c = self.sql.cursor()
        with open("secret/venus_mariadb_bulkinsert.txt", mode='r', encoding='utf-8') as f:
            print("Iniciando iteração para bulkinsert")
            for line in f:
                line = line.rstrip()
                
                # Checando se é uma query válida pra mim.
                if line == "":
                    print("Linha vazia.")
                    continue
                elif line.startswith('--'):
                    print("Linha comentada.")
                    continue
                elif line.lower().startswith('insert'): # pode ser um bottleneck eventualmente
                    print(f"> executando: {line}")
                    c.execute(line)
                else:
                    print(f"\nLinha inválida, desconsiderando:\n{line}\n")
                self.sql.commit()
        print(f"Arquivo iterado completamente.")
        
def dev():
    pass

if __name__ == "__main__":
    print("CUIDADO! DEVE RODAR ESTE SCRIPT DIRETO SOMENTE COM INTENÇÃO DE TESTE EM LOCAL ESPECÍFICO.")
    dev()

#pip install mysql.connector