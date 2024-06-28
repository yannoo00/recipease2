from flask import Flask, render_template, request, jsonify
from chatbot import chatbot_bp

app = Flask(__name__, static_folder='static')
app.register_blueprint(chatbot_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()