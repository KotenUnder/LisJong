import LisJongUtils
import json

MJLOGGER_HEADER = '<mjloggm ver="2.3">'
MJLOGGER_FOOTER = "</mjloggm>"





class MjLogger:

    def __init__(self, outputpath_, pnames_):
        self._outlet = open(outputpath_, "w")


    def write_game(self, **info):
        pass


    def end_match(self, **info):
        pass


    def output(self):
        pass


class TenhouMjLog(MjLogger):
    def __init__(self, outputpath_, pnames_):
        super.__init__(outputpath_, pnames_)
        shuffler = {"seed":"mt19937ar-sha512-n288-base64,HJ79I8EV", "ref":""}
        self._outlet.write(xmlize("SHUFFLE", **shuffler))
        go = {"type":"169", "lobby":0}
        self._outlet.write(xmlize("GO", **go))
        un = {
            "n0":pnames_[0], "n1":pnames_[1], "n2":pnames_[2], "n3":pnames_[3],
            "dan":"16,16,16,16", "rate":"2000.00,2000.00,2000.00,2000.00",
            "sx":"M,M,M,M"
        }
        self._outlet.write(xmlize("UN", **un))
        taikyoku = {"oya":0}
        self._outlet.write(xmlize("TAIKYOKU", **taikyoku))



class DennoJson(MjLogger):
    def __init__(self, outputpath_, pnames_, title_):
        super().__init__(outputpath_, pnames_)
        self._outlet.close()
        self._outlet = open(outputpath_, "w", encoding="utf-8")

        self._main = {}
        self._main["title"] = title_
        self._main["player"] = pnames_
        self._main["qijia"] = 0
        self._main["log"] = []


    def write_game(self, **info):
        game = []
        gameinfo = {}

        # 点数と初期配牌を決定する
        iniscorelist = [0] * 4
        inihandlist = [0] * 4

        for abid in range(4):
            iniscorelist[relativize(abid, info["game"])] = info["initial_score"][abid]
            inihandlist[relativize(abid, info["game"])] = lisjong_to_tenhou(info["initial_hand"][abid])

        #配牌情報
        game.append(
            {
                "qipai":{
                    "zhuangfeng":info["round"],
                    "jushu":info["game"],
                    "changbang":info["extra"],
                    "lizhibang":info["deposit"],
                    "defen":iniscorelist,
                    "baopai":lisjong_to_tenhou(info["dora1_indicator"]),
                    "shoupai":inihandlist,
                }
            }

        )

        id_offset = info["game"]

        for action in info["actions"]:
            if action["action"] == "draw":
                game.append(
                    {
                        "zimo":{"l":relativize(action["plid"], id_offset) , "p":lisjong_to_tenhou(action["tile"])}
                    }
                )
            elif action["action"] == "discard":
                discarded = lisjong_to_tenhou(action["tile"])
                if action["riichi"]:
                    discarded += "*"
                if action["tsumogiri"]:
                    discarded += "_"
                game.append(
                    {
                        "dapai":{"l":relativize(action["plid"], id_offset), "p":discarded}
                    }
                )


        # 対局結果
        # 点数変化の相対化
        scorediff = [0] * 4
        for abid in range(4):
            scorediff[relativize(abid, info["game"])] = info["score_diff"][abid]

        # ロン上がり
        if "win" in info and info["win"]["winby"] == "Ron":
            wincase = info["win"]
            wincomment = wincase["score"][1]
            fu = 30
            han = 5
            if "fu" in wincomment:
                fu = int(wincomment[0:2])
                han = int(wincomment[4])
            game.append(({
                "hule":{
                    "l":relativize(wincase["winner"], id_offset),
                    "shoupai":lisjong_to_tenhou(wincase["hand"]) + lisjong_to_tenhou(wincase["winning_tile"]),
                    "baojia":relativize(wincase["payer"], id_offset),
                    # TODO 符を正しくする　Utilsまで変更が波及してしまう
                    "fu":fu,
                    "fanshu":han,
                    "defen":int(wincase["score"][0]),
                    "hupai":self.make_yakulist(wincase["score"][2]),
                    "fenpei":scorediff
                },
            }))

        elif "win" in info and info["win"]["winby"] == "Tsumo":
            wincase = info["win"]
            wincomment = wincase["score"][1]
            fu = 30
            han = 5
            if "fu" in wincomment:
                fu = int(wincomment[0:2])
                han = int(wincomment[4])
            parts = wincase["score"][0].split("-")
            if len(parts) > 1:
                purescore = 2* int(parts[0]) + int(parts[1])
            else:
                purescore = 3 * int(wincase["score"][0][0:-3])

            game.append(({
                "hule":{
                    "l":relativize(wincase["winner"], id_offset),
                    "shoupai":lisjong_to_tenhou(wincase["hand"]) + lisjong_to_tenhou(wincase["winning_tile"]),
                    # TODO 符を正しくする　Utilsまで変更が波及してしまう
                    "fu":fu,
                    "fanshu":han,
                    "defen":purescore,
                    "hupai":self.make_yakulist(wincase["score"][2]),
                    "fenpei":scorediff
                },
            }))


        # 流局
        elif "draw" in info:
            # 手配の並び替えとフォーマット変換
            shoupai = [0] * 4
            scorediff = [0] * 4
            for abid in range(4):
                shoupai[relativize(abid, info["game"])] = lisjong_to_tenhou(info["draw"]["hand"][abid])
                scorediff[relativize(abid, info["game"])] = info["score_diff"][abid]

            if info["draw"]["name"] == "Goulash":
                game.append({
                    "pingju": {
                        "name": "荒牌平局",
                        "shoupai": shoupai,
                        "fenpei": scorediff
                        }})



        self._main["log"].append(game)


    def end_match(self, **info):
        self._main["defen"] = info["score"]
        self._main["rank"] = info["rank"]
        self._main["point"] = info["point"]

    def output(self):
        json.dump(self._main, self._outlet, ensure_ascii=False)
        self._outlet.close()


    def make_yakulist(self, yakulist_):
        dennnolist = []

        for yaku in yakulist_:
            if "Dora" not in yaku:
                dennnolist.append({
                    "name":YAKU_DICTIONARY[yaku][1],
                    "fanshu":YAKU_DICTIONARY[yaku][0]
                })
            else:
                dennnolist.append({
                    "name":YAKU_DICTIONARY[yaku[0:-2]][1],
                    "fanshu":int(yaku[-1])
                })

        return dennnolist


def xmlize(title_, **kwargs):
    body = ""
    for key in kwargs:
        body += ' {0}="{1}"'.format(key, str(kwargs[key]))
    return "<{0} {1}/>".format(title_, body)


def relativize(absolute_id_, dealer_id_):
    return (absolute_id_ - dealer_id_) % 4


def lisjong_to_tenhou(haistr_):
    #0のこともあって並び替え
    haistr_ = LisJongUtils.arrange_tile(haistr_)

    ms = []
    ps = []
    ss = []
    zs = []
    #mpszで分類する
    for i in range(int(len(haistr_) / 2)):
        hai_class = haistr_[i*2+1]
        if hai_class == "m":
            ms.append(haistr_[i * 2])
        elif hai_class == "p":
            ps.append(haistr_[i * 2])
        elif hai_class == "s":
            ss.append(haistr_[i * 2])
        elif hai_class == "z":
            zs.append(haistr_[i * 2])

    tenhou = ""
    if len(ms) > 0:
        tenhou += "m" + "".join(ms)
    if len(ps) > 0:
        tenhou += "p" + "".join(ps)
    if len(ss) > 0:
        tenhou += "s" + "".join(ss)
    if len(zs) > 0:
        tenhou += "z" + "".join(zs)

    return tenhou


YAKU_DICTIONARY = {
    "Ready":[1,"立直"],
    "One Shot":[1,"一発"],
    "Pure Self-Pick":[1, "門前清自摸和"],
    "Peace": [1, "平和"],
    "1Peko":[1, "一盃口"],
    "All Simples":[1,"断么九"],
    "Last Pick":[1, "海底摸月"],
    "Last Discard":[1, "河底撈魚"],
    "Honor Tile - White":[1,"役牌　白"],
    "Honor Tile - Green": [1,"役牌　發"],
    "Honor Tile - Red": [1,"役牌　中"],
    "Prevailing Wind":[1,"役牌　場風牌"],
    "Own Wind":[1,"役牌　自風牌"],

    "Chanta": [2, "混全帯么九"],
    "Chanta (open)":[1, "混全帯么九"],
    "Straight": [2, "一気通貫"],
    "3 Color Straights": [2, "三色同順"],
    "3 Concealed Triplets": [2, "三暗刻"],
    "3 Color Triplets":[2, "三色同刻"],


    "Semi-Flush":[3,"混一色"],
    "Semi-Flush (open)":[2, "混一色"],
    "Junchan":[3,"純全帯么九"],
    "2Peko":[3,"二盃口"],
    "Flush":[6,"清一色"],
    "Flush (open)":[5,"清一色"],

    "Dora":[None,"ドラ"],
    "Underneath Dora":[None,"裏ドラ"],
    "Red Dora":[None,"赤ドラ"]
}
