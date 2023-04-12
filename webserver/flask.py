from flask import Flask, redirect, url_for, render_template, request, session, flash
from functools import wraps
from utilidade.venutils import sha1, lerArquivo, venLog
from datetime import timedelta

log = venLog()

class VenusWS:
    def __init__(self, database):

        log.info(f"Setando o cliente DB")
        self.venusdb = database # quando quero usar os métodos de VenusDB, ações / querys automaticas
        self.database = database.sql # conexão mysql, para fazer ações / querys manuais
        log.info(f"Iniciando FLASK APP")
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
                self.token = self.venusdb.validateLogin(user, passwd)
                
            def get_session_info(self):
                self.info = self.venusdb.getSessionInfo(self.token)

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
                
                if lambda self: False if not self.info['superuser'] else True:
                    # print("-debug- É Admin.")
                    self.info['valid_cards'] = self.venusdb.getInstancesForOrg([self.info['organization_id']], admin=True)
                    return self.info['valid_cards']
                else:
                    # print("-debug- Não é admin.")
                    self.info['valid_cards'] = self.venusdb.getInstancesForOrg([self.info['organization_id']]) # Não salvo em nenhum lugar, bate diretamente no banco-de-dados sempre que faz essa requisição.
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
        
            
        def login_required(f): # Precisa estar LOGADO
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not user_session.validate_session():
                    print(f"route [{f.__name__}]: login_required: user IS NOT logged in")
                    flash("Você precisa estar logado para acessar esta página!", "info")
                    return redirect(url_for("login"))
                print(f"route [{f.__name__}]: login_required: user IS logged in")
                return f(*args, **kwargs)
            return decorated_function
        
        def superuser_required(f): # Precisa estar LOGADO, e ser um SUPERUSER
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not user_session.validate_session():
                    print(f"route [{f.__name__}]: superuser_required: user IS NOT logged in")
                    flash("Você precisa estar logado para acessar esta página!", "info")
                    return redirect(url_for("login"))
                print(f"route [{f.__name__}]: superuser_required: user IS logged in")
                if not user_session.info['superuser']:
                    # não é admin
                    print(f"route [{f.__name__}]: superuser_required: user IS NOT admin")
                    flash("Você não tem permissão para acessar esta página.", "info")
                    return redirect(url_for('user_homepage'))
                # é admin
                print(f"route [{f.__name__}]: superuser_required: user IS admin")
                return f(*args, **kwargs)
            return decorated_function
        
        # INICIO Misc-Wrappers (Wrappers específicos para rotas)
        
        def can_load_card(f): # Precisa estar LOGADO
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # if not {algo que determina que session pode usar current_card_id}:
                    #não pode ver o card
                # else:
                # pode ver o card
                return f(*args, **kwargs)
            return decorated_function


        # FIM Misc-Wrappers

        @app.route("/") 
        @login_required
        def home():
            return redirect(url_for("user_homepage"))


        print("teste")

        # Página inicial do usuário
        @app.route("/homepage/")
        @login_required
        def user_homepage():
                
            # Isso daqui faz uma requisição ao banco. O ideal seria, em user_session.get_orgs_for_session(), eu fazer uma consulta se essas informações já estão na sessão. se já estiver, utilizo-as. caso não esteja, puxo do banco e adiciono na sessão, na parte user_session.info['display_orgs'], caso contrário toda vez que acessar homepage vai ter uma sessão gerada
            
            # Não funciona, pois ao fazer alteração no banco com uma sessão gerada, as atualizações do banco não passariam pra sessão, fazendo ter um usuário 'de-sincronizado' com o sistema...
            
            return render_template("index.html", 
                                   cardlist=user_session.get_orgs_for_session(), # sempre que atualizo a página, requisito o banco de dados
                                   userIsAdmin=user_session.userIsAdmin())


        @app.route("/instance/<id>/", methods=['GET'])
        @login_required
        def instance(id):            
            host_id = id
            
            return render_template("instance.html", userIsAdmin=user_session.userIsAdmin())


        # Página de login + lógica
        @app.route('/login/', methods=['GET', 'POST'] )
        def login():
            if request.method == "POST": # Se for um POST
                username = request.form['inputUsername'] # Usuário
                password = sha1(request.form['inputPassword']) # Senha encriptada
                user_session.validate_login(username, password) # Uso a classe de banco de dados, método validateLogin()
                if (user_session.token != None):
                    
                    session['token'] = user_session.token # Inicio a sessão
                    if request.form.get('lembrar'): # Se marcou para lembrar sua sessão (limite 8h = expediente)
                        session.permanent=True
                    else:
                        session.permanent=False
                    flash("Login bem sucedido!", "info")
                    return redirect(url_for('user_homepage'))
                else:
                    flash("Login inválido!", "info") 
                    return render_template('login.html')      
                    
            else: # É um GET
                if user_session.validate_session(): # Já está logado
                    return redirect(url_for("user_homepage"))
                
                
                return render_template('login.html')

        
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
        
        
        @app.route("/admin/")
        @superuser_required # só pode ser chamado se tiver passado pelo login_required
        def admin():      
            
            return render_template("admin.html") 


        @app.route("/dev/")
        @superuser_required
        def navbar():
            # talvez criar um custom render template onde consigo colocar informações que sempre são necessárias de se ter, no caso, userIsAdmin
            return render_template("dev.html", userIsAdmin=user_session.userIsAdmin())
        

        return app
