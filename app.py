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
    language = data.get("language", "c").lower()

    if language not in ("c", "python"):
        return jsonify({"error": f"Unsupported language: '{language}'. Choose 'c' or 'python'."}), 400

    try:
        tokens = lexer(code, language)
        parser = Parser(tokens, language)
        result = parser.parse()
        return jsonify({"pseudocode": result, "language": language})
    except SyntaxError as e:
        return jsonify({"error": f"Syntax error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Parse error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
