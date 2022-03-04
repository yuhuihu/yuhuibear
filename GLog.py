#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
" misc for simulation.
"""

import inspect
import sys
import os
import time
import numpy
import rich
import pdbr

"""
报错专用函数
"""

_logoutStream = sys.stdout


class ElapsedWatch:
    def __init__(self):
        self.name2elapsed = {}
        self.runningTag = set()
        self.initmil = int(round(time.time() * 1000))

    def Start(self, tag):
        self.name2elapsed[tag] = int(round(time.time() * 1000))
        self.runningTag.add(tag)

    def Stop(self, tag):
        if tag in self.name2elapsed:
            self.runningTag.remove(tag)
            self.name2elapsed[tag] = int(round(time.time() * 1000)) - self.name2elapsed[tag]
        else:
            self.name2elapsed[tag] = 0
        return self.name2elapsed[tag]

    def Elasped(self, tag=None):
        """
        查询tag事件过去的豪秒数

        :param tag [string]: 唯一标识这个计时
        """
        if tag in self.name2elapsed:
            return int(round(time.time() * 1000)) - self.name2elapsed[tag]
        elif tag is None:
            return int(round(time.time() * 1000)) - self.initmil
        else:
            return 0

    def __str__(self):
        sumv = sum([v for k, v in self.name2elapsed.items() if k not in self.runningTag])
        mstr = f"Elasped:{int(round(time.time() * 1000)) - self.initmil} "

        for n, v in self.name2elapsed:
            mstr += f"{n}:{v} ({v / sumv * 100:>.1f}%) "
        return mstr

    def __repr__(self):
        return self.__str__()


_rich_console = rich.console.Console()


class LogSeting:
    logStackStrip = 0
    sysRunningTime = time.time()

    @staticmethod
    def GetConsole():
        return _rich_console

    @staticmethod
    def PrintStack(tag, level=3, skip=0):
        _rich_console.print(f"[bold red]{tag}>>")
        for idx, st in enumerate(inspect.stack()):
            if skip > 0 and idx < skip:
                continue
            if level < 0:
                return
            else:
                level -= 1
            tstr = [str(st[idx]) for idx in range(1, len(st))]
            _rich_console.print("\t{:d}|{:s}".format(idx, "|".join(tstr)), file=_logoutStream)


def _directLog(head, fmt, *args, **kws):
    dt = time.time() - LogSeting.sysRunningTime
    stacks = inspect.stack()
    sidx = 2 + LogSeting.logStackStrip
    if sidx >= len(stacks):
        sidx = max(0, len(stacks) - 1)
        _rich_console.print_exception(show_locals=True)

        # _rich_console.print(len(stacks), sidx, LogSeting.logStackStrip, file=_logoutStream)
        # for st in stacks:
        # _rich_console.print("\t", st, file=_logoutStream)

    funname = str(stacks[sidx][3])
    if head == "E":
        head = f"[bold red]{head}[/]"
    tfmt = f"{dt:>6.2f}|{head}|{funname}|".format(funname)
    if isinstance(fmt, str) and len(args) > 0 and len(kws) == 0:
        targs = []
        for ag in args:
            if type(ag) not in [int, float, str, numpy.float64]:
                targs.append(str(ag))
            else:
                targs.append(ag)
        try:
            _rich_console.print(tfmt + fmt.format(*args))
        except ValueError as e:
            for idx, t in enumerate(targs):
                _rich_console.print(f"{idx:2d}| type:{type(t)} value:{t}")
            raise e
    elif not isinstance(fmt, str) and len(args) == 0 and len(kws) == 0:
        _rich_console.print(tfmt)
        _rich_console.print(fmt)
    else:
        objs = [tfmt]
        if fmt is not None:
            objs.append(fmt)
        if args is not None:
            objs.extend(args)
        if kws is not None:
            for k, v in kws.items():
                objs.append(k)
                objs.append(v)
        _rich_console.print(*objs)


def LogContinue(fmt, *args):
    _rich_console.print(fmt.format(*args), file=_logoutStream, flush=True)


def Log(fmt, *args):
    _directLog("I", fmt, *args)


def LogStack():
    _rich_console.print_exception(show_locals=True)


def LogError(fmt, *args):
    _directLog("E", fmt, *args)
    # try:
    # _rich_console.print_exception(show_locals=True)
    # except Exception:
    # catch exception for printing of stack
    # pass


def PrintCellError(sheet, row, col, msg, *args):
    msghead = "表单[{:s}], row:{:d} col:{:d}".format(sheet.name, (row + 1), (col + 1))
    msghead += ":" + msg
    LogError(msghead, *args)


def PrintEnumError(sheet, row, col, enum, errorname):
    PrintCellError(
        sheet,
        row,
        col,
        "枚举[" + enum.name + "]中没有枚举值:" + (errorname is not None and errorname or "[]"),
    )


def _g_exceptionHook(type, value, tb):
    """
    excepthook for automatic debugging
    checks env for PYTHON_DEBUG
    if NO then nothing happens
    otherwise use the regular pdb module
    or specify ipdb for a more interactive version

    :param type [TODO:type]: [TODO:description]
    :param value [TODO:type]: [TODO:description]
    :param tb [TODO:type]: [TODO:description]
    :raises Exception: [TODO:description]
    """
    if hasattr(sys, "ps1") or not sys.stderr.isatty() or not sys.stdin.isatty():
        # stdin or stderr is redirected, just do the normal thing
        original_hook(type, value, tb)
    else:
        # a terminal is attached and stderr is not redirected, debug
        try:
            _rich_console.print(f"error:{type}, {value}")
            ctb = tb
            # breakpoint()
            while ctb is not None:
                _rich_console.print(ctb.tb_frame.f_code)
                ctb = ctb.tb_next
            # skip = 0
            # level = 10
            # for idx, st in enumerate(inspect.stack()):
                # if skip > 0 and idx < skip:
                    # continue
                # if level < 0:
                    # break
                # else:
                    # level -= 1
                # tstr = [str(st[idx]) for idx in range(1, len(st))]
                # _rich_console.print("\t{:d}|{:s}".format(idx, "|".join(tstr)), file=_logoutStream)
            pdbr.pm()
        except Exception:
            pass


# automatically debug unless stdout/stderr redirected via stack overflow
# ! note that python3 has more rigid scopes so you might not see everything you want
original_hook = sys.excepthook
# setting PYTHON_DEBUG to NO suppresses any debugging
if sys.excepthook == sys.__excepthook__ and not os.environ.get("PYTHON_DEBUG", "pdbr") in ["NO", "no"]:
    # if someone already patched excepthook, let them win
    sys.excepthook = _g_exceptionHook
    pass
