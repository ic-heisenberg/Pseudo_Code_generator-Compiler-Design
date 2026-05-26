from flask import Flask, request, jsonify, send_from_directory
from parser_file import lexer, Parser

app = Flask(__name__)

# Serve frontend
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# API endpoint
@app.route("/parse", methods=["POST"])
def parse_code():
    data = request.get_json()
    code = data.get("code", "")

    try:
        tokens = lexer(code)
        parser = Parser(tokens)
        result = parser.parse()
        return jsonify({"pseudocode": result})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)