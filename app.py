from flask import Flask, render_template, request, jsonify
from chatbot import chatbot_bp

app = Flask(__name__, template_folder='build/templates', static_folder='build/static')
app.register_blueprint(chatbot_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()