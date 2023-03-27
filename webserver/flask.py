from flask import Flask, redirect, url_for, render_template, request, session, flash
from utilidade.venutils import sha1, lerArquivo#, venlog
from datetime import timedelta

#log = venLog()

class VenusWS:
    def __init__(self, database):

        #log.info(f"Setando o cliente DB")
        self.venusdb = database # quando quero usar os métodos de VenusDB, ações / querys automaticas
        self.database = database.sql # conexão mysql, para fazer ações / querys manuais
        #log.info(f"Iniciando FLASK APP")
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
                         
            
        app = Flask(__name__)
        app.secret_key = lerArquivo("secret/venus_mariadb_senha.txt", encrypt_sha1=True)
        app.permanent_session_lifetime = timedelta(hours=8)
        user_session=SessionManager(session, self.venusdb, None, None)
        user_session.token = None
        user_session.info = None
        
        def checkSession():
            return user_session.validate_session()
            
        def getSessionInfo(token:str):
            return self.venusdb.getSessionInfo(token)
            

        @app.route("/") 
        def home():
            return redirect(url_for("user_homepage"))


        # Página inicial do usuário
        @app.route("/homepage/")
        def user_homepage():
            if not checkSession(): # Não está LOGADO
                return redirect(url_for("login"))
                
                
            return render_template("index.html")


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
                    session.permanent=True
                    flash("Login bem sucedido!", "info")
                    return redirect(url_for('user_homepage'))
                else:
                    flash("Login inválido!", "info") 
                    return render_template('login.html')          
            else: # É um GET
                if checkSession(): # Já está logado
                    return redirect(url_for("user_homepage"))
                
                
                return render_template('login.html')
        
        
        @app.route('/logout/')
        def logout():
            if not checkSession(): # Não está LOGADO
                return redirect(url_for("login"))


            # Está logado, logo, encerro a sessão.
            session.pop('token', None) # Removo o token
            session.pop('info', None)
            user_session.session.pop('token', None)
            user_session.session.pop('info', None)
            user_session.token=None
            user_session.info=None
            #user_session.token, user_session.info = None # Removo as informações da sessão (não preciso disso por causa do checkSession)
            flash("Deslogado com sucesso!", "info")
            return redirect(url_for('login')) # Envio para página de login

        
        @app.route("/admin/")
        def admin():      
            if not checkSession(): # Não está LOGADO
                return redirect(url_for("login"))
            if not user_session.info['superuser']: # Está logado, tem sessão, mas não é ADMIN
                flash("Você não tem permissão para acessar esta página.", "info")
                return redirect(url_for('user_homepage'))
            

            return render_template("admin.html") 


        return app
