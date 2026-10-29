from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')


if __name__ == '__main__':
    app.run(debug=True)
