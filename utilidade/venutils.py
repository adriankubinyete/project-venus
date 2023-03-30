from datetime import datetime
import hashlib
import logging
import paramiko

class CustomSSH_KeyDoesntExist(Exception):
    # Autenticação por chave falhou (pois o arquivo/path da chave não existe), e não tem / não pode autenticar por senha.
    pass

class CustomSSH_KeyFailed(Exception):
    # Autenticação por chave falhou, e não tem / não pode autenticar por senha.
    pass

class CustomSSH_ConnectException(Exception):
    # Todos os métodos de autenticação que estavam disponíveis falharam.
    pass

class CustomSSH_CloseFailed(Exception):
    # Por algum motivo, não foi possível fechar a conexão SSH.
    pass

class CustomSSH_BadExitStatus(Exception):
    # O Exit-Status recebido do comando não está dentro da lista de acceptable_exit_statuses
    pass

class CustomSSH_Exception(Exception):
    # Exception geral
    pass

class CustomSSH(object):
    
    def __init__(self, ip:str, user:str, password:str=None, key:str=None, port:int=22):
        # Organization Info
        self.ip = ip
        self.port = port # 22 ou VALUE
        self.user = user
        self.password = password # None ou VALUE
        self.key = key # None ou VALUE
        
        self.cmd_history = {}
        self.last_cmd = {} # Dicionário que é sobreescrito com o ultimo comando do send_cmd. keys [comando, resultado, exit_status, host]
        
        if key:
            self.can_use_key = True
        else:
            self.can_use_key = False
            
        if password:
            self.can_use_password = True
        else:
            self.can_use_password = False
            
        # PMK Session
        self.ssh = paramiko.client.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.using_ssh = False
        
    def connect(self, timeout:int=60):
        
        # Tenta autenticar por chave. Se der errado, tenta por senha (se tiver), e então sobe erro.
        try:
            if self.can_use_key:
                self.ssh.connect(
                    self.ip, 
                    username=self.user, 
                    password=self.password,
                    port=self.port,
                    key_filename=self.key)  
            elif self.can_use_password:
                self.ssh.connect(
                    self.ip,
                    username=self.user,
                    password=self.password,
                    port=self.port,
                    look_for_keys=False
                )
            else:
                raise paramiko.AuthenticationException
        except paramiko.AuthenticationException as e:
            if self.can_use_key:
                print("Autenticação por chave falhou, tentando autenticação por senha....")
                self.can_use_key = False
                if self.can_use_password:
                    self.connect()
                else:
                    raise CustomSSH_KeyFailed(f"Autenticação pela chave \"{self.key}\"falhou!\n{e}")
            else:
                if self.can_use_password:
                    # se está neste exception, já tentou a chave mas não conseguiu, então tentou a senha mas falhou também...
                    raise CustomSSH_ConnectException(f"Todos os métodos de autenticação falharam!\n{e}")
        except FileNotFoundError as e:
            self.can_use_key = False
            if self.can_use_password:
                #log.error(f"Chave \"{self.key}\" não existe, mas prosseguindo pois há uma senha para autenticação: \"{self.password}\"") # "Tiny Error (é um erro, mas é ignorável pois há 'cobertura')"
                self.connect()
            else:
                raise CustomSSH_KeyDoesntExist(f"A chave \"{self.key}\" não existe.")
        finally:
            self.using_ssh = True # Está com uma conexão ssh ativa
        
    def close(self):
        try:
            self.ssh.close()
        except Exception as e:
            raise CustomSSH_CloseFailed(f"Houve algum erro ao tentar fechar a conexão SSH!\n{e}")
        finally:
            self.using_ssh = False
    
    def send_cmd(self, cmd:str, timeout:int=180, acceptable_exit_statuses:list=[0, 1]):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout, get_pty=True)
            response = stdout.read().decode('utf-8')
            exit_status = int(stdout.channel.recv_exit_status())
            
            # Registrando no "histórico" do objeto
            cmd_history_number = len(self.cmd_history) + 1
            result = {
                "id": f"{cmd_history_number}",
                "comando": f"{cmd}",
                "resultado": f"{response}",
                "exit_status": f"{exit_status}",
                "host": f"{self.ip}",
            }
            self.cmd_history[f'cmd_{cmd_history_number}'] = result
            self.last_cmd = result
            
            if exit_status not in acceptable_exit_statuses:
                raise CustomSSH_BadExitStatus(f"O retorno do comando {cmd} foi diferente do retorno aceitável ({acceptable_exit_statuses})")
        except CustomSSH_BadExitStatus:
            raise
        except Exception as e:
            raise CustomSSH_Exception(f"Algum erro aconteceu ao enviar o comando {cmd}...\n{e}")
        

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
    LOG_FILE = f"utilidade/logfile-{datetime.now().strftime('%d-%m-%y')}.log"
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.DEBUG,
        format='[%(asctime)s] <%(levelname)s> : %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    return logging.getLogger(__name__)