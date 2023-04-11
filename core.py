from database.dbc import VenusDB
from webserver.flask import VenusWS
from utilidade.venutils import sha1, lerArquivo, venLog
import asyncio

# Teste interno
def dev():
    print('hello')


def main():
    log = venLog()
    log.info("INICIANDO")
    
    venusdb = VenusDB(
        db_host=lerArquivo("secret/venus_mariadb_host.txt"), 
        db_user=lerArquivo("secret/venus_mariadb_usuario.txt"), 
        db_pass=lerArquivo("secret/venus_mariadb_senha.txt", encrypt_sha1=True),
        db_database=lerArquivo("secret/venus_mariadb_database.txt")
        )

    venusws = VenusWS(venusdb)
    venusws.app.run(host='0.0.0.0', debug=True)
        
if __name__ == "__main__":
    main()