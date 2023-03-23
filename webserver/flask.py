from flask import Flask, redirect, url_for

# devo fazer isso em classe, provavelmente...

class VenusWS:
    def __init__(self):
        self.app = self.start_Flask()
        
    def start_Flask(self):
        app = Flask(__name__)

        @app.route("/") # Diz pro flask que ao acessar "/" é pra rodar esta função.
        def home():
            return "<h1>hello, world</h1>"

        @app.route("/<nome>/")
        def user(nome):
            return f"olá, {nome}!<br>"

        @app.route("/<user>--<teste>/")
        def my_test(user, teste):
            return f"olá {user}! <br> o valor de teste é {teste}"

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
