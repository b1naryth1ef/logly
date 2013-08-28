from flask import Flask, request
from database import *
from datetime import datetime

app = Flask(__name__)

@app.route("/get")
def route_get(): pass

if __name__ == "__main__":
    app.run(debug=True)
