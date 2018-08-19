from flask import Flask
from flask import render_template

app = Flask(__name__)
app.debug = True

@app.route("/")
def hello():
    return render_template('hello.html',message="Hey hey hey!")

@app.route("/example")
def example():
    return "new route created and it's working"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

