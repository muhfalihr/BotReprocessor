import os
from utility import kang_util

from flask import Flask, Response, render_template_string

util = kang_util()
app = Flask(__name__)
config = util.get_config(__file__)

@app.route('/log')
def log_page():
    return render_template_string("""
    <!doctype html>
    <html>
    <head>
        <title>BotReprocessLog</title>
        <link rel="icon" href="static/favicon.png" type="image/png">
        <style>
            body {
                background-color: black;
                color: white;
                font-family: monospace;
            }
            pre {
                white-space: pre-wrap;
                word-wrap: break-word;
            }
        </style>
        <script>
            function refreshLog() {
                fetch('/log-content')
                    .then(response => response.text())
                    .then(data => {
                        let logElement = document.getElementById('log');
                        logElement.innerText = data.split("\\n").reverse().join("\\n");
                    });
            }
            setInterval(refreshLog, 1000);
            window.onload = refreshLog;
        </script>
    </head>
    <body>
        <pre id="log"></pre>
    </body>
    </html>
    """)

@app.route('/log-content')
def get_log_content():
    log_path = f'{config["LOG_PATH"]}/debug.log'
    if os.path.exists(log_path):
        with open(log_path, 'rb') as log_file:
            log_content = log_file.read().decode('utf-8')
        return Response(log_content, mimetype='text/plain')
    else:
        return Response('Log file not found', status=404, mimetype='text/plain')

if __name__ == "__main__":
    app.run(host=config["HOST"], port=config["PORT"], debug=True)
