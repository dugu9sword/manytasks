import os
import time

from colorama import Back, Fore
from tabulate import tabulate
from manytasks import shared


class Color(object):
    @staticmethod
    def red(s):
        return Fore.RED + str(s) + Fore.RESET

    @staticmethod
    def green(s):
        return Fore.GREEN + str(s) + Fore.RESET

    @staticmethod
    def yellow(s):
        return Fore.YELLOW + str(s) + Fore.RESET

    @staticmethod
    def blue(s):
        return Fore.BLUE + str(s) + Fore.RESET

    @staticmethod
    def magenta(s):
        return Fore.MAGENTA + str(s) + Fore.RESET

    @staticmethod
    def cyan(s):
        return Fore.CYAN + str(s) + Fore.RESET

    @staticmethod
    def white(s):
        return Fore.WHITE + str(s) + Fore.RESET

    @staticmethod
    def white_green(s):
        return Fore.WHITE + Back.GREEN + str(s) + Fore.RESET + Back.RESET


def log(*info, target='cf'):
    assert target in ['c', 'f', 'cf', 'fc']
    info_str = str("\n".join(info))
    if 'c' in target:
        print(info_str)
    if 'f' in target:
        logger = globals()["__logger__"]
        logger.write("{}\n".format(info_str))
        logger.flush()


def log_config(filename, log_path, append=False):
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    logger = open("{}/{}.txt".format(log_path, filename),
                  "a" if append else "w")
    globals()["__logger__"] = logger


def current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def draw_logo():
    log("""
    =================================================================
                                      _____              _         
          /\/\    __ _  _ __   _   _ /__   \  __ _  ___ | | __ ___ 
         /    \  / _` || '_ \ | | | |  / /\/ / _` |/ __|| |/ // __| 
        / /\/\ \| (_| || | | || |_| | / /   | (_| |\__ \|   < \__ \ 
        \/    \/ \__,_||_| |_| \__, | \/     \__,_||___/|_|\_\|___/ 
                               |___/                               
    =================================================================
    """)

def show_task_list():
    log(">>>>>> Show the task list...")
    keys = []
    for task in shared.tasks:
        for arg in task:
            if arg.key not in keys:
                keys.append(arg.key)

    header = ['idx'] + keys
    # header = list(map(Color.cyan, header))
    table = [header]
    for idx, task in enumerate(shared.tasks):
        # log("\t{} : {}".format(idx, arg2str(arg_group)), target='cf')
        values = []
        for key in keys:
            found = False
            for arg in task:
                if arg.key == key:
                    found = True
                    values.append(arg.value)
                    break
            if not found:
                values.append("-")
        table.append([idx] + values)
    log(tabulate(table))
    log()