from flask import Flask


app = Flask(__name__)

@app.route('/')
def home():
    return "Flask heroku app"

@app.route('/home')
def asd():
    print("asd")
    return "done"

if __name__ == "__main__":
    app.run()