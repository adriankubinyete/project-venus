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
                # fazer uma lógica de 
                # if not self.info['display_orgs']: # (não tem orgs pra dar display)
                #   self.venusdb.getInstancesForOrg([self.info['organization_id']])
                # else:
                #   pass ?
                return self.venusdb.getInstancesForOrg([self.info['organization_id']])
                
            # ideia: fazer algo tipo session_update(self), que atualiza todas informações (se não tiver, puxa do banco, se tiver, não faz nada)
            # as informações a receberem update, seria basicamente todo o session.info
            
            # pensando em reestruturar esse código do session manager, pensar em algo mais conciso, refatorar / ver se dá pra melhorar alguma coisa no session manager, tendo em mente que sempre que acessa um site, tem que validar informações
            
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
       
        def render_cards_template(template_name, **kwargs):
            card_list = user_session.get_orgs_for_session()
            #print(f"Card list in render_cards_template: {card_list}") # debug
            return render_template(template_name, cardlist=card_list, **kwargs)
                
        def userHasSession():
            return user_session.validate_session()
        
        def userIsAdmin():
            if not user_session.info['superuser']:
                return False
            else:
                return True
            
        def getSessionInfo(token:str):
            return self.venusdb.getSessionInfo(token)
            
        def login_required(f): # apenas uma função teste para ser usada como template aqui
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if session.get('username') is None or session.get('if_logged') is None:
                    return redirect('/login',code=302)
                return f(*args, **kwargs)
            return decorated_function

        @app.route("/") 
        def home():
            return redirect(url_for("user_homepage"))


        # Página inicial do usuário
        @app.route("/homepage/")
        def user_homepage():
            if not userHasSession(): # Não está LOGADO
                return redirect(url_for("login"))
                
            # Isso daqui faz uma requisição ao banco. O ideal seria, em user_session.get_orgs_for_session(), eu fazer uma consulta se essas informações já estão na sessão. se já estiver, utilizo-as. caso não esteja, puxo do banco e adiciono na sessão, na parte user_session.info['display_orgs'], caso contrário toda vez que acessar homepage vai ter uma sessão gerada
            
            return render_cards_template("index.html")


        # Página de login + lógica
        @app.route('/login/', methods=['GET', 'POST'] )
        def login():
            if request.method == "POST": # Se for um POST
                username = request.form['inputUsername'] # Usuário
                password = sha1(request.form['inputPassword']) # Senha encriptada
                user_session.validate_login(username, password) # Uso a classe de banco de dados, método validateLogin()
                if (user_session.token != None):
                    
                    # JOGAR UM DICIONÁRIO DO USER_CONFIG NESSA SESSION.TOKEN
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
                if userHasSession(): # Já está logado
                    return redirect(url_for("user_homepage"))
                
                
                return render_template('login.html')
        
        
        @app.route('/logout/')
        def logout():
            if not userHasSession(): # Não está LOGADO
                return redirect(url_for("login"))


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
        def admin():      
            if not userHasSession(): # Não está LOGADO
                return redirect(url_for("login"))
            if not userIsAdmin(): # Está logado, tem sessão, mas não é ADMIN
                flash("Você não tem permissão para acessar esta página.", "info")
                return redirect(url_for('user_homepage'))
            
            return render_template("admin.html") 

        @app.route("/dev/")
        def navbar():
            return render_template("dev.html")
        return app
