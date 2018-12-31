from alchemist import glob
from flask import Flask, url_for, send_file
import json

app = Flask(__name__, static_folder='web', static_url_path='/web')


@app.route("/bootstrap.min.css")
def bst_css():
    return send_file('web/bootstrap.min.css')


@app.route("/bootstrap.min.js")
def bst_js():
    return send_file('web/bootstrap.min.js')


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
