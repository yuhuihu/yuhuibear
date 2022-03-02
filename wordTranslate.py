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
from typing import List, Dict
import os
import yaml


class Linestr(yaml.YAMLObject):
    yaml_tag = "Linestr"

    def __init__(self, fn: str, lnu: List[int], wds: List[str]):
        self.fname = fn
        self.locs = lnu
        self.words = wds

    def __repr__(self):
        return f"{fn}, locs:[{locs}],lines:{self.words}"


def CountInDir(ddir: str, ignore: List[str]) -> List:

    f2locs = []
    wordset = set()
    line2locs = {"":[]}

    if not os.path.exists(ddir):
        return f2locs
    else:
        igset = set(ignore)
        re_ch = re.compile(r"[\u4e00-\u9fa5]*")
        re_quat = re.compile(r'".*"')
        totalch = 0
        dirstack = [ddir]
        while len(dirstack) > 0:
            cdir = dirstack.pop()
            for fn in os.listdir(cdir):
                if fn[0] == ".":
                    continue
                elif fn in igset:
                    continue
                cfn = os.path.join(cdir, fn)
                if os.path.isfile(cfn):
                    chcnt = 0

                    flines = []
                    fws = []
                    with open(cfn, mode="r", encoding="utf8") as cf:
                        # recs = []
                        for il, l in enumerate(cf):
                            hasch = False
                            for ic, tw in enumerate(re_ch.findall(l)):
                                if len(tw) > 0:
                                    hasch = True
                                    chcnt += len(tw)

                                    # recs.append((ic, ic + len(tw), tw))
                                    wordset.add(tw)
                            if hasch:
                                for tl in re_quat.findall(l):
                                    if len(tl) < 1:
                                        continue
                                    words = tl[1: -1]
                                    if len(words) > 0:
                                        if words in line2locs:
                                            line2locs[words].append((cfn, il))
                                        else:
                                            line2locs[words] = [(cfn, il)]
                                        fws.append(words)
                                        flines.append(il)
                        # rprint(f"file: {cfn} chs: {recs}")
                        if chcnt > 0:
                            rprint(f"file: {cfn} chs: {chcnt}")
                            f2locs.append(Linestr(cfn, flines, fws))
                    totalch += chcnt
                elif os.path.isdir(cfn):
                    dirstack.append(cfn)
    return f2locs, wordset, line2locs, totalch


if __name__ == "__main__":

    igs = [
        "conf_sensitive_word.lua",
        "conf_age_notice.lua",
        "conf_user_agreement.lua",
    ]
    f2tags = dict(
        config_items="item",
        config_npc="npc",
    )
    f2loc, wset, line2loc, chcnt = CountInDir("../../unity/pack-host/Assets/config/", igs)


    wcnt = 0
    for tw in wset:
        wcnt += len(tw)

    outfname = "ch_loc_list.yaml"
    with open(outfname, "w") as of:
        yaml.dump(
            line2loc,
            of,
            encoding="utf-8",
            allow_unicode=True,
        )
    with open("ch_line_list.csv", "w") as of:
        for i, (line, flnus) in enumerate(line2loc.items()):
            of.write(f"{i:>5d}|{line}\n")

    rprint(
        f"chs: {chcnt} chwords: {wcnt} chlines: {len(line2loc)} output list({len(f2loc)}) to {outfname}"
    )
