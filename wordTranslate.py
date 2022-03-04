#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pwcount.py
#
#
# created by yuhui.
# @三  2/23 11:59:15 2022

import sys
import re
import datetime
from rich import print as rprint
from typing import List, Dict, Tuple, Set
import os
import yaml
from rich.progress import Progress
from GLog import Log, LogError


class Linestr(yaml.YAMLObject):
    yaml_tag = "Linestr"

    def __init__(self, fn: str, lnu: List[int], wds: List[str]):
        self.fname = fn
        self.locs = lnu
        self.words = wds

    def __repr__(self):
        return f"{self.fname}, locs:[{self.locs}],lines:{self.words}"


class WordRef(yaml.YAMLObject):
    yaml_tag = "WordRef"

    def __init__(
        self,
        fn: str,
        lnu: int,
        strcode: int,
        orgWords: str = None,
        color: str = None,
        colorbg: Tuple[int] = None,
        colorend: Tuple[int] = None,
        tag: str = "",
    ):
        self.fname = fn
        self.linenu = lnu
        self.orgWords = orgWords
        self.color = None
        self.colorBg = colorbg
        self.colorEnd = colorend
        self.tag = tag
        self.hashcode = strcode

    def __repr__(self):
        return f"{self.fname}:{self.linenu} tag: {self.tag} color:{self.colorBg}-{self.colorEnd}"


def ListAllFile(ddir: str, igset: Set[str]):
    fs = []
    dirstack = [(ddir, "")]
    while len(dirstack) > 0:
        (cdir, sn) = dirstack.pop()
        for fn in os.listdir(cdir):
            if fn[0] == ".":
                continue
            if fn in igset:
                continue
            cfn = os.path.join(cdir, fn)
            if fn[-4:] == ".lua":
                fn = fn[:-4]
            if os.path.isdir(cfn):
                dirstack.append((cfn, fn))
            else:
                fs.append((cfn, fn))
    return fs


def CountInDir(ddir: str, ignore: List[str], f2tags: Dict[str, Dict[str, str]]):

    # f2locs = []
    wordset: Dict[str, str] = {}
    word2locs: Dict[str, List[WordRef]] = {}

    if not os.path.exists(ddir):
        return {}, {}, 0

    igset = set(ignore)
    re_ch = re.compile(r"[\u4e00-\u9fa5]*")
    re_quat = re.compile('".*"')
    re_color1 = re.compile(r"<color\s*=\s*#[a-zA-Z0-9]{5,8}\s*>")
    re_color2 = re.compile(r"</color\s*>")
    totalch = 0

    flist = ListAllFile(ddir, igset)
    # flist = [("./conf_test.lua", 'conf_test')]
    # with Progress() as progress:
    # tsk1 = progress.add_task("extract language", total=len(flist))

    for fidx, (cfn, fn) in enumerate(flist):
        chcnt = 0
        with open(cfn, mode="r", encoding="utf8") as cf:
            # recs = []
            tagdict = f2tags[fn] if fn in f2tags else None
            for il, line in enumerate(cf):
                hasch = False
                for tl in re_quat.findall(line):
                    if len(tl) < 1:
                        continue
                    words = tl[1:-1]
                    if len(words) < 1:
                        continue
                    chmatch = re_ch.search(words, 0)
                    if chmatch is None:
                        continue
                    sp = chmatch.span()
                    if sp[0] == sp[1]:
                        continue

                    chcnt += len(words)

                    wordkey = words
                    wtran = words

                    rec = WordRef(cfn, il, hash(wordkey))
                    if tagdict is not None:
                        for treg, tname in tagdict.items():
                            rret = re.search(f'\s*{treg}\s*=\s*"', line)
                            if rret is not None:
                                tidx = rret.span()
                                if tidx[0] != tidx[1]:
                                    rec.tag = tname
                                    break

                    mk_color = re_color1.search(words, 0)
                    if mk_color:
                        cidx = mk_color.span()
                        rec.colorBg = cidx
                        rec.color = words[cidx[0] : cidx[1]]
                        wordkey = re_color1.sub("", wordkey)
                        wtran = re_color1.sub("&{", wtran)

                    mk_color_end = re_color2.search(words, 0)
                    if mk_color_end:
                        rec.colorEnd = mk_color_end.span
                        wordkey = re_color2.sub("", wordkey)
                        wtran = re_color2.sub("&}", wtran)

                    if rec.hashcode in word2locs:
                        word2locs[rec.hashcode].append(rec)
                    else:
                        word2locs[rec.hashcode] = [rec]

                    if len(rec.tag) > 0 and wordkey in wordset:
                        ptag = wordset[wordkey][1]
                        if len(ptag) > 0 and ptag != rec.tag:
                            # breakpoint()
                            LogError(
                                f"different tag |prv: {wordset[wordkey][1]}| now: {rec.tag}| with the same words: [{wordkey}], {rec}"
                            )
                    wordset[wordkey] = (wtran, rec.tag, rec.hashcode)
        totalch += chcnt
        # progress.update(tsk1, advance=1, description=f'extract file {fidx:4}/{len(flist)} words: {len(wordset)} characters: {totalch}')
        Log(
            f"extract file {fidx:4}/{len(flist)} words: {len(wordset)} characters: {totalch}"
        )
    key2tran = [(k, v) for k, v in wordset.items()]
    key2tran.sort(key=lambda x: x[0])
    return key2tran, word2locs


f2tags = dict(# {{{
    config_items={
        "name": "道具名",
        "desc": "道具描述",
    },
    config_item_type={
        "desc": "道具类型",
    },
    config_npc={
        "name": "NPC名称",
        "talk_content": "npc对白",
    },
    conf_test={
        "name": "NPC名称",
        "talk_content": "npc对白",
    },
    config_task={
        "name": "任务名称",
        "desc": "任务剧情描述",
        "target_desc": "任务目标描述",
        "type_desc": "任务类型",
        "finish_desc": "任务结束描述",
        "finish_dailogue": "任务结束对白",
    },
    config_mount={
        "name": "坐骑名称",
    },
    conf_achievement={
        "title": "成就名称",
        "desc": "成就描述",
    },
    conf_achievement_subtype={
        "name": "成就子类型",
    },
    conf_achievement_type={
        "name": "成就类型",
    },
    conf_career={
        "name": "职业名称",
    },
    conf_shop={
        "name": "商店商品名称",
    },
    conf_sys_function={
        "name": "系统功能名称",
    },
    conf_sys_function_foretell={
        "name": "系统功能名称",
        "main_text": "系统功能说明",
        "second_text": "系统功能说明",
        "third_text": "系统功能说明",
    },
    confi_top_arena_dan={
        "name": "颠覆竞技段位名称",
    },
    config_bag={
        "name": "背包类型",
    },
    config_beast_power={
        "name": "兽灵名称",
    },
    config_chat_emoji={
        "text": "表情文字",
        "tag": "表情名称",
    },
    config_equip_suit={
        "name": "套装名称",
    },
    config_fashion={
        "name": "时装名称",
    },
    config_guild_skill={
        "name": "工会技能名称",
        "attr_name": "工会技能作用属性",
    },
    config_seal={
        "name": "方尊名称",
        "chapter_name": "章节名称",
        "chap_title": "章节标题",
        "chap_content": "章节主题",
        "chap_desc": "章节剧情",
    },
    config_skill={
        "name": "技能名称",
        "desc": "效果描述",
        "desc_long": "效果描述",
    },
)# }}}

if __name__ == "__main__":

    igs = [
        "conf_sensitive_word.lua",
        "conf_age_notice.lua",
        "conf_user_agreement.lua",
        "config_name.lua",  # 1-5 组名字组成,  额外给到 3组名字组成, 每组超过100个上下名字(单字多字均可)
    ]

    wset, line2loc = CountInDir("../../unity/pack-host/Assets/config/", igs, f2tags)

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
    with open("words_translate.csv", "w") as of:
        of.write(f"odrer|tag|hash code|source text\n")
        for i, (key, ch_tag) in enumerate(wset):
            msg = f"{i:>5d}|{ch_tag[1]}|{ch_tag[2]}|{ch_tag[0]}\n"
            of.write(msg)
            # Log(msg)

    Log(
        f"chwords: {wcnt} keys: {len(wset)} chlines: {len(line2loc)} output list to {outfname}"
    )
