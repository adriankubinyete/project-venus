from database.dbc import VenusDB
from webserver.flask import VenusWS
from utilidade.venutils import sha1, lerArquivo, venLog
import asyncio

def main():
    log = venLog()
    log.info("INICIANDO")
    venusdb = VenusDB(
        db_host=lerArquivo("secret/venus_mariadb_host.txt"), 
        db_user=lerArquivo("secret/venus_mariadb_usuario.txt"), 
        db_pass=lerArquivo("secret/venus_mariadb_senha.txt", encrypt_sha1=True)
        )
    venusws = VenusWS(venusdb) # Inicio o WS conectado a este DB
    venusws.app.run()
        
if __name__ == "__main__":
    main()