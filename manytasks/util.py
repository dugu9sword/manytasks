from colorama import Fore, Back
import os
import time


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
