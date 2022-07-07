from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources=r'/*')
import json



@app.route('/',methods=['POST'])#这里设置一下ajax的url
def ba():
    data = request.json.get('text')
    data = eval(data)
    filename = "target.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

app.run(host='127.0.0.1',port=5002)
