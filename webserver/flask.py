from flask import Flask, redirect, url_for, render_template, request, session, flash
from functools import wraps
from utilidade.venutils import sha1, lerArquivo, venLog
from datetime import timedelta

log = venLog()

class VenusWS:
    def __init__(self, database):

        self.venusdb = database # quando quero usar os métodos de VenusDB, ações / querys automaticas
        self.database = database.sql # conexão mysql, para fazer ações / querys manuais
        log.info(f"Iniciando FLASK APP")
        print('Iniciando FLASK APP')
        self.app = self.start_flask()
    
    def start_flask(self):
        class SessionManager:
            def __init__(self, session, db, token, info):
                self.session = session
                self.venusdb = db
                self.token = token
                self.info = info
                
            def userIsAdmin(self):
                if not self.info['superuser']:
                    return False
                else:
                    return True

            def validate_login(self, user, passwd):
                log.debug(f"Validando login de \"{user}\"")
                self.token = self.venusdb.validateLogin(user, passwd)
                
            def get_session_info(self):
                log.debug(f"Obtendo sessão...")
                self.info = self.venusdb.getSessionInfo(self.token)
                log.debug(f"Sessão obtida: {self.info}")

            def validate_session(self):
                if 'token' in self.session:
                    self.token = self.session['token']
                    if self.info == None:
                        self.get_session_info()
                    return True
                else:
                    return False
                
            def get_orgs_for_session(self):
                # print(f"Obtendo as instâncias a serem exibidas na lista de cards, para o usuário \"{self.info['screen_name']}\".")
                
                log.debug(f"Obtendo hosts para \"{self.info['screen_name']}\": superuser={self.info['superuser']}")
                                             
                if self.info['superuser'] == True:
                    self.info['valid_cards'] = self.venusdb.getInstancesForOrg([self.info['organization_id']], admin=True)
                    log.debug(f"Hosts válidos para \"{self.info['screen_name']}\": \"{self.info['valid_cards']}\"")
                    return self.info['valid_cards']
                else:
                    self.info['valid_cards'] = self.venusdb.getInstancesForOrg([self.info['organization_id']]) # Não salvo em nenhum lugar, bate diretamente no banco-de-dados sempre que faz essa requisição.
                    log.debug(f"Hosts válidos para \"{self.info['screen_name']}\": \"{self.info['valid_cards']}\"")
                    return self.info['valid_cards'] # Atualiza sempre que faz a requisição ao banco. Usado para definir permissões de cards ao tentar acessar via URL, um card que não estiver nessa lista retornará uma página inválida (Não pode acessar este card)
        
            
        app = Flask(__name__)
        app.secret_key = lerArquivo("secret/venus_mariadb_senha.txt", encrypt_sha1=True)
        app.permanent_session_lifetime = timedelta(hours=8)
        user_session=SessionManager(session, self.venusdb, None, None)
        user_session.token = None
        user_session.info = None
       
        @app.context_processor # Utility para poder printar dentro do JINJA2 > mdebug('msg'/var)
        def utility_functions():
            def print_in_console(message):
                print(str(message))
            return dict(mdebug=print_in_console)
        
        # misc functions para wrappers
        def redirect_if_not_logged(destino:str):
            if not user_session.validate_session(): # Não está logado
                    flash("Você precisa estar logado para acessar esta página!", "info")
                    return redirect(url_for(destino))
        def redirect_if_not_superuser(destino:str):
            if not user_session.info['superuser']: # Não é SUPERUSER
                    flash("Você não tem permissão para acessar esta página.", "info")
                    return redirect(url_for(destino))
            
        # wrappers gerais
        def login_required(f): # PRECISA ESTAR LOGADO
            @wraps(f)
            def decorated_function(*args, **kwargs):
                redirect_if_not_logged('login') # Se não estiver logado, vai pra 'login'
                return f(*args, **kwargs)
            return decorated_function
        
        def superuser_required(f): # PRECISA ESTAR LOGADO E SER SUPERUSER
            @wraps(f)
            def decorated_function(*args, **kwargs):
                redirect_if_not_logged('login') # Se não estiver logado, vai pra 'login'
                redirect_if_not_superuser('instance_list') # Se não estiver logado, vai pra 'instance_list'
                return f(*args, **kwargs) # Está logado, e é um SUPERUSER.
            return decorated_function

        # Homepage do usuário da sessão. Ainda não implementado.
        @app.route("/home/") 
        @login_required
        def home():
            return redirect(url_for("instance_list"))


        # Lista de instâncias para usuário da sessão.
        @app.route("/instances/")
        @login_required
        def instance_list():
            return render_template("instances.html", 
                cardlist=user_session.get_orgs_for_session(), # sempre que atualizo a página, requisito o banco de dados
                userIsAdmin=user_session.userIsAdmin())


        # Página para consultar instância X
        @app.route("/instances/<host_id>/", methods=['GET', 'POST'])
        @login_required
        def instances(host_id:int):
            
            def can_load_instance():
                instance_id = host_id
                valid_ids=[]

                if 'valid_cards' in user_session.info: # Tem cards.
                    log.debug(f"[SESSION \"{user_session.info['screen_name']}\"] Tem cards. Coletando ID.")
                    for valid_card in user_session.info['valid_cards']:
                        card_id = valid_card[0] # valid_cards é uma lista com várias listas, e o index 0 dessas inner-lists é sempre o ID daquele card (empresa, host)
                        valid_ids.append(str(card_id))
                        
                else: # Não tem cards. Faço uma consulta no banco e tento denovo.
                    log.debug(f"[SESSION \"{user_session.info['screen_name']}\"] Não tem cards. Gerando e coletando ID.")
                    user_session.get_orgs_for_session() # gero os cards
                    for valid_card in user_session.info['valid_cards']:
                        card_id = valid_card[0] # valid_cards é uma lista com várias listas, e o index 0 dessas inner-lists é sempre o ID daquele card (empresa, host)
                        valid_ids.append(str(card_id))
                        
                log.debug(f"[SESSION \"{user_session.info['screen_name']}\"] IDs Válidos: {valid_ids}")
                log.debug(f"[SESSION \"{user_session.info['screen_name']}\"] ID Solicitado: {instance_id}")
                log.debug(f"[SESSION \"{user_session.info['screen_name']}\"] ID Válido? {instance_id in valid_ids}")

                if instance_id in valid_ids:
                    log.debug(f"[SESSION \"{user_session.info['screen_name']}\"] Acesso liberado para a instância de ID \"{instance_id}\"")
                    return True
                else:
                    flash('Você não tem permissão para acessar esta página!')
                    return False 
            
            if request.method == "POST": # POST --------------------------------------------------------------
                
                if not can_load_instance():
                    flash('Você não tem permissão para acessar esta página!')
                    return redirect(url_for("instance_list")) 
                
                host_name = request.form['host_name']
                host_host = request.form['host_host']
                host_dns = request.form['host_dns']
                host_ssh_port = request.form['host_ssh_port']
                host_ssh_user = request.form['host_ssh_user']
                host_ssh_password = request.form['host_ssh_password']
                
                print(f'''name = {host_name}
host = {host_host}
dns = {host_dns}
ssh_port = {host_ssh_port}
ssh_user = {host_ssh_user}
ssh_password = {host_ssh_password}''')
                
                # Envia o comando para atualizar as informações da instância
                user_session.venusdb.updateInstance(
                host_id=host_id,
                host_name=host_name,
                host_host=host_host,
                host_dns=host_dns,
                host_ssh_port=host_ssh_port,
                host_ssh_user=host_ssh_user,
                host_ssh_password=host_ssh_password) # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                
                flash(f"Informações da empresa \"{host_id}\" atualizadas!")
                return redirect(request.url) # Entra na mesma página
            
            else: # GET --------------------------------------------------------------
            
                if not can_load_instance():
                    flash('Você não tem permissão para acessar esta página!')
                    return redirect(url_for("instance_list")) 
                    
                return render_template("instance.html", userIsAdmin=user_session.userIsAdmin(), hostInfo=user_session.venusdb.getInstance(host_id))           


        # Página para Login.
        @app.route('/login/', methods=['GET', 'POST'] )
        def login():
            if request.method == "POST": # Se for um POST
                username = request.form['inputUsername'] # Usuário
                password = sha1(request.form['inputPassword']) # Senha encriptada
                user_session.validate_login(username, password) # Uso a classe de banco de dados, método validateLogin()
                if (user_session.token != None): # login deu certo
                    
                    session['token'] = user_session.token # Inicio a sessão
                    if request.form.get('lembrar'): # Se marcou para lembrar sua sessão (limite 8h = expediente)
                        session.permanent=True
                    else:
                        session.permanent=False
                    flash("Login bem sucedido!", "info")
                    return redirect(url_for('instance_list'))
                else: # login falhou
                    flash("Login inválido!", "info") 
                    return render_template('login.html')      
                    
            else: # É um GET
                if user_session.validate_session(): # Já está logado
                    return redirect(url_for("instance_list"))
                
                
                return render_template('login.html')

        
        # Página para desautenticação de uma sessão.
        @app.route('/logout/')
        @login_required
        def logout():
            
            # Está logado, logo, encerro a sessão.
            session.pop('token', None) # Removo o token
            session.pop('info', None)
            user_session.session.pop('token', None)
            user_session.session.pop('info', None)
            user_session.token=None
            user_session.info=None
            #user_session.token, user_session.info = None # Removo as informações da sessão (não preciso disso por causa do userHasSession)
            flash("Deslogado com sucesso!", "info")
            return redirect(url_for('login')) # Envio para página de login
        
        
        # Página de administrador.
        @app.route("/admin/")
        @superuser_required
        def admin():      
            return render_template("admin.html") 


        # Página de desenvolvimento.
        @app.route("/dev/")
        @superuser_required
        def navbar():
            # talvez criar um custom render template onde consigo colocar informações que sempre são necessárias de se ter, no caso, userIsAdmin
            return render_template("dev.html", userIsAdmin=user_session.userIsAdmin())
        

        return app
