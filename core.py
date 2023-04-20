from database.dbc import VenusDB
from webserver.flask import VenusWS
from utilidade.venutils import sha1, lerArquivo, venLog
import asyncio

# Teste interno
def dev():
  pass

def main():
    log = venLog()
    log.info("INICIANDO")
    
    venusdb = VenusDB(
        db_host=lerArquivo("secret/venus_mariadb_host.txt"), 
        db_user=lerArquivo("secret/venus_mariadb_usuario.txt"), 
        db_pass=lerArquivo("secret/venus_mariadb_senha.txt", encrypt_sha1=True),
        db_database='venus',
        noselect=True
        )
    
    venusdb.purge_database() # deixar isso descomentado somente em carater de desenvolvimento
    venusdb.boot_database_configuration() # re-crio toda estrutura de tabelas
    venusdb.bulk_insert() # insiro algumas informações de teste pra gerar cards

    venusws = VenusWS(venusdb)
    venusws.app.run(host='0.0.0.0', debug=True) # Por algum motivo que não tá no meu conhecimento, se "debug=True", ele vai rodar as linhas de cima 2x, causando IntegrityError no insert, se não tiverem comentadas (purge, boot e bulk_insert) 🤡
        
if __name__ == "__main__":
    main()