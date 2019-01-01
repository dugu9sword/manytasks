from alchemist import glob
from flask import Flask, url_for, send_file, send_from_directory
import json
import socket
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def available_port():
    for port in range(5000, 5010):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("127.0.0.1", port))
            # s.shutdown(2)
            # print(port)
        except:
            return port
    raise Exception("No port available")


app = Flask(__name__, static_folder='web', static_url_path='/web')


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('web/js', path)


@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('web/css', path)


@app.route("/")
def index():
    return send_file('web/index.html')


@app.route("/task")
def task():
    return json.dumps({"task_name": glob.task_name,
                       "executor": glob.executor,
                       "runnable": glob.runnable,
                       "cuda": glob.cuda,
                       "concurrency": glob.concurrency})


def arg2str(arg_group):
    return " ".join(list(map(lambda arg: "{}={}".format(arg.key, arg.value), arg_group)))


@app.route("/status")
def status():
    ret = {}
    for i, arg_group in enumerate(glob.arg_group_list):
        ret[arg2str(arg_group)] = glob.arg_group_status[i]
    return json.dumps(ret)


if __name__ == '__main__':
    app.run()
