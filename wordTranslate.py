#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pwcount.py
#
#
# created by yuhui.
# @三  2/23 11:59:15 2022

import sys
import re
from rich import print as rprint
from typing import List
import os
import yaml


def CountInDir(ddir) -> List:

    p2w = []
    wset = set()
    lineset = set()
    if not os.path.exists(ddir):
        return p2w
    else:
        re_ch = re.compile(r"[\u4e00-\u9fa5]*")
        re_quat = re.compile(r'".*"')
        totalch = 0
        dirstack = [ddir]
        while len(dirstack) > 0:
            cdir = dirstack.pop()
            for fn in os.listdir(cdir):
                if fn[0] == ".":
                    continue
                elif fn in ["conf_sensitive_word.lua", "conf_age_notice.lua", "conf_user_agreement.lua"]:
                    continue
                cfn = os.path.join(cdir, fn)
                if os.path.isfile(cfn):
                    chcnt = 0
                    with open(cfn, mode="r", encoding="utf8") as cf:
                        rec = []
                        for il, l in enumerate(cf):
                            isch = False
                            for ic, tw in enumerate(re_ch.findall(l)):
                                if len(tw) > 0:
                                    isch = True
                                    chcnt += len(tw)
                                    rec.append((ic, ic + len(tw), tw))
                                    wset.add(tw)
                            if isch:
                                for tl in re_quat.findall(l):
                                    if len(tl) > 0:
                                        lineset.add(tl[1:-1])
                        # rprint(f"file: {cfn} chs: {rec}")
                        if chcnt > 0:
                            rprint(f"file: {cfn} chs: {chcnt}")
                            p2w.append((cfn, il, rec))
                    totalch += chcnt
                elif os.path.isdir(cfn):
                    dirstack.append(cfn)
    return p2w, wset, lineset, totalch


if __name__ == "__main__":

    recs, wset, lineset, chcnt = CountInDir("./pack-host/Assets/config/")

    wcnt = 0
    for tw in wset:
        wcnt += len(tw)

    outfname = "ch_loc_list.yaml"
    with open(outfname, "w") as of:
        yaml.dump(
            recs,
            of,
            encoding="utf-8",
            allow_unicode=True,
        )
    with open("ch_line_list.txt", 'w') as of:
        for i, l in enumerate(lineset):
            of.write(f"{i:>5d} {l}\n")

    rprint(
        f"chs: {chcnt} chwords: {wcnt} chlines: {len(lineset)} output list({len(recs)}) to {outfname}"
    )
