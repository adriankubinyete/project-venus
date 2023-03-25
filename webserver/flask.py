from flask import Flask, redirect, url_for, render_template, request, session
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

        def checkSession():
            if 'id' in session: # Se houver uma sessão, mostro a página (usuário logado)
                return True
            else:
                return False

        @app.route("/") # Diz pro flask que ao acessar "/" é pra rodar esta função.
        def home():
            return redirect(url_for("user_homepage"))


        # Página inicial do usuário
        @app.route("/homepage/")
        def user_homepage():
            if not checkSession(): # se não existir uma sessão, envia pra login
                return redirect(url_for("login"))
                
            return render_template("index.html")

        @app.route('/login/', methods=['GET', 'POST'] )
        def login():
            if request.method == "POST": # Se for um POST
                username = request.form['inputUsername'] # Usuário
                password = sha1(request.form['inputPassword']) # Senha
                userId = self.venusdb.validateLogin(username, password) # uso o cliente do db
                if (userId != None):
                    # checo se usuario e senha está correto
                    # tupla no DB onde fica registrada todas informações do usuário
                    
                    # retorna essa tupla inteira como uma lista/dic e usa isso como 'global user_session'
                    # retorna as informações da conta (db)
                    session['id'] = userId # criando uma sessão pra esse usuário
                    session.permanent=True
                    return redirect(url_for('user_homepage'))
                else:
                    print("LOGIN INVÁLIDO")  
                    return render_template('login.html')          
            else: # É um GET
                if 'id' in session: # Já tem um token de sessão
                    return redirect(url_for('user_homepage'))
                
                else: # Não tem um token de sessão, precisa logar-se
                    return render_template('login.html')
        
        
        
        @app.route('/logout/')
        def logout():
            if 'id' in session: # Há um token na sessão
                session.pop('id', None) # Removo o token
                return redirect(url_for('login')) # Envio para página de login
            else:
                return redirect(url_for('login')) # Não está logado, vai para login.
        
        @app.route("/admin/")
        def admin():
            # envia para a url /<nome>, e seta nome para "Admin!". o keyword passado deve bater o mesmo nome
            # de argumento que está configurado /<name>
            return redirect(url_for("user", name="Admin!"))

        # ideia tipo @app.route("/login")
        # @app.route("/home/central/<id-card>/<acao>"), 
        # dessa forma eu posso criar uma template, sem ter que criar manualmente cada id,
        # e ao dar redirect, eu passo o valor de id-card e acao

        #url_for = pegar o path, o URL que dá até aquela função.
        return app
