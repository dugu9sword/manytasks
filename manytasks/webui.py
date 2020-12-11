from manytasks import shared
from flask import Flask, url_for, send_file, send_from_directory
import json
import socket
import logging
import os
from tailer import tail
import pynvml
import sys

# cli = sys.modules['flask.cli']
# cli.show_server_banner = lambda *x: None

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def init_gpu_handles():
    gpu_handles = {}
    try:
        pynvml.nvmlInit()
        for cid in shared.cuda:
            gpu_handles[cid] = pynvml.nvmlDeviceGetHandleByIndex(cid)
    except Exception:
        pass
    globals()["gpu_handles"] = gpu_handles


def available_port():
    for port in range(5000, 5010):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("127.0.0.1", port))
            # s.shutdown(2)
            # print(port)
        except Exception:
            return port
    raise Exception("No port available")


app = Flask(__name__, static_folder='web', static_url_path='/web')


@app.route('/gpu_info')
def gpu_info():
    # ret = {"0": {"used": 3057.0, "total": 12189.9375, "util": 19}, "1": {"used": 11339.0, "total": 12189.9375, "util": 60}, "2": {"used": 9077.0, "total": 12189.9375, "util": 100}}
    # return json.dumps(ret)
    ret = {}
    gpu_handles = globals()["gpu_handles"]
    for key in gpu_handles:
        handle = gpu_handles[key]
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        ret[key] = {
            "used": "{:.2f}".format(mem_info.used / (1024 * 1024)),
            "total": "{:.2f}".format(mem_info.total / (1024 * 1024)),
            "util": gpu_util.gpu
        }
    return json.dumps(ret)


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('web/js', path)


@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('web/css', path)


@app.route("/")
def index():
    return send_file('web/index.html')


@app.route("/log-<int:task_id>-tail-<int:tail_num>")
def fetch_log(task_id, tail_num):
    log_path = "{}/task-{}.txt".format(shared.log_path, task_id)
    if os.path.exists(log_path):
        return "\n".join(tail(open(log_path), tail_num))
    else:
        return "Log not found."

@app.route("/task")
def task():
    return json.dumps({"task_name": shared.task_name,
                       "executor": shared.executor,
                       "runnable": shared.runnable,
                       "cuda": shared.cuda,
                       "concurrency": shared.concurrency})


@app.route("/status")
def status():
    ret = {}
    for i, task in enumerate(shared.tasks):
        ret[i] = {
            "args": shared.task2str(task),
            "status": shared.task_status[i]
        }
    return json.dumps(ret)


if __name__ == '__main__':
    init_gpu_handles()
    app.run(host="0.0.0.0")
