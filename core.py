from database.dbc import VenusDB
from webserver.flask import VenusWS
from utilidade.venutils import sha1, lerArquivo, venLog
import asyncio

# Teste interno
def dev():
    def unpackList(list): 
        ret = ''
        for i in range(0, len(list)):
            print(f'iterando: {i}, tamanho da lista: {len(list)}')
            # se for o ultimo item, adiciono sem ","
            if i == len(list)-1:
                ret+=f'{list[i]}'
            # se não for o ultimo item, adiciono com ","
            else:
                ret+=f'{list[i]}, '
        return ret
    # SELECT id, instance, host, dns FROM organization_info WHERE organization_id IN ()
    orgs = [1]
    print(unpackList(orgs))


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