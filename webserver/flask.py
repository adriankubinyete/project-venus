from flask import Flask, redirect, url_for, render_template, request, session, flash
from utilidade.venutils import sha1, lerArquivo#, venlog
from datetime import timedelta

#log = venLog()

class VenusWS:
    def __init__(self, database):
        #log.info(f"Iniciando FLASK APP")
        self.app = self.start_Flask()
        #log.info(f"Setando o cliente DB")
        self.venusdb = database # quando quero usar os métodos de VenusDB, ações / querys automaticas
        self.database = database.sql # conexão mysql, para fazer ações / querys manuais
        
    def start_Flask(self):
        
        app = Flask(__name__)
        app.secret_key = lerArquivo("secret/venus_mariadb_senha.txt", encrypt_sha1=True)
        app.permanent_session_lifetime = timedelta(hours=8)
        userToken = None
        
        # Checo se já tem uma sessão existente. Caso tenha, atribuo o token da lógica ao token que está vivo
        def checkSession():
            nonlocal userToken
            if 'token' in session: # Se houver uma sessão, mostro a página (usuário logado)
                userToken = session['token']
                return True
            else:
                return False

        def checkAdminPrivileges():
            nonlocal userToken
            if self.venusdb.adminPrivileges(userToken):
                return True
            else:
                return False
            






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
            nonlocal userToken
            if request.method == "POST": # Se for um POST
                username = request.form['inputUsername'] # Usuário
                password = sha1(request.form['inputPassword']) # Senha encriptada
                userToken = self.venusdb.validateLogin(username, password) # Uso a classe de banco de dados, método validateLogin()
                if (userToken != None):
                    session['token'] = userToken # Inicio a sessão
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
            flash("Deslogado com sucesso!", "info")
            return redirect(url_for('login')) # Envio para página de login

        
        @app.route("/admin/")
        def admin():      
            if not checkSession(): # Não está LOGADO
                return redirect(url_for("login"))
            if not checkAdminPrivileges(): # Está logado, mas não é ADMIN
                flash("Você não tem permissão para acessar esta página.", "info")
                return redirect(url_for('user_homepage'))
            
            
            return render_template("admin.html") 



        # ideia tipo @app.route("/login")
        # @app.route("/home/central/<id-card>/<acao>"), 
        # dessa forma eu posso criar uma template, sem ter que criar manualmente cada id,
        # e ao dar redirect, eu passo o valor de id-card e acao

        #url_for = pegar o path, o URL que dá até aquela função.
        return app
