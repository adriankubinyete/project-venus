from database.dbc import VenusDB
from utilidade.venutils import sha1, ler_arquivo
from webserver.flask import VenusWS
import asyncio

def main():
    vdb = VenusDB(
        db_host=ler_arquivo("secret/venus_mariadb_host.txt"), 
        db_user=ler_arquivo("secret/venus_mariadb_usuario.txt"), 
        db_pass=ler_arquivo("secret/venus_mariadb_senha.txt", encrypt_sha1=True)
        )
    vws = VenusWS()
    print(vws.app.run()) # Após o RUN, nenhum comando passa.
    
if __name__ == "__main__":
    main()