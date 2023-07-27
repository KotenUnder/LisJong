# This is a sample Python script.
import datetime
import hashlib
import numpy as np
import time
import psutil
import socket
import threading
import LisJongUtils
import mjlogger
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


TILE_TOTAL = 4 * (9+9+9+7)
DEADWALL_COUNT = 14
PLAYER_COUNT = 4
POSITION_DORA = TILE_TOTAL - 5
WIND_TABLE = ["1z", "2z", "3z", "4z"]
TEMPAI_ADVANTAGE = 3000


# Server側からの情報を格納するためのクラス
class PlayersInfo:
    def __init__(self, name_, initial_score_=25000):
        self.names = [name_[plid] for plid in range(4)]
        self.scores = [initial_score_] * 4
        self.newgame()

    def newgame(self):
        self.hands = [""] * 4
        self.exposes = [[], [], [], []]
        self.ponds = [[], [], [], []]
        self.riichi_flag = [""] * 4
        self.oneshot_flag = [""] * 4

    def sorthand(self):
        for hand in self.hands:
            hand.sort(key=LisJongUtils.tile_index)


    def loot(self, plid_, draw_, discard_):
        if draw_ == discard_:
            return
        if not discard_ in self.hands[plid_]:
            print(self.hands[plid_], discard_)
            raise Exception
        self.hands[plid_].remove(discard_)
        self.hands[plid_].append(draw_)

class Janshi():
    def __init__(self, name_, initial_score_=25000):
        self.name = name_
        self.score = initial_score_

        self.newgame()

    def newgame(self):
        self.hand = []
        self.exposes = [[],[],[],[]]
        self.doras = []
        self.ponds = [[],[],[],[]]
        self.riichi_flag = False
        self.oneshot_flag = False


    def initial_draw(self, initial13str_):
        self.hand = []
        for i in range(13):
            self.hand.append(initial13str_[i*2:i*2+2])

    # キル杯を返す
    def draw(self, draw_pai_, riichi_=[], tsumo_=False, kong_=[]):
        command, discard_tile, tsumogiri_flag = self.engine_discard(draw_pai_, riichi_, tsumo_, kong_)

        if command == "Tsumo":
            return "Tsumo", draw_pai_, tsumogiri_flag

        # 立直中で上がらないあれば自摸切り絶対
        if self.riichi_flag:
            tsumogiri_flag = True


        # 自摸切り判断
        if not discard_tile in self.hand:
            tsumogiri_flag = True

        # 自摸切りでなく、ちゃんとあるばあいに
        if not tsumogiri_flag:
            if discard_tile in self.hand:
                discard_id = self.hand.index(discard_tile)
                self.hand[discard_id] = draw_pai_

        # 自分が立直中なら、command修正
        if self.riichi_flag:
            command = "Discard"
            discard_tile = draw_pai_
            tsumogiri_flag = True

        return command, discard_tile, tsumogiri_flag


    def draw_called(self):
        pass
#        return "Discard", discard_tile, False


    def call(self, discarded_, choice_, message_):
        # そのまま投げて、結果を確認してから返す
        action = self.engine_call(discarded_, choice_, message_)
        if action[0] == "Ron":
            return action
        elif action[0] == "Chii":
            return "Chii", action[1]
        elif action[0] == "Pon":
            return action
        elif action[0] == "Kan":
            return action
        else:
            return "Skip", []


    def inform_call(self, turnplayer_relative_, discarded_, callplayer_relative_, voice_, exposed_):
        #すでに巣手配処理は去れていると考えて

        #巣手配に対して追加する
        self.ponds[callplayer_relative_].append(exposed_)

    def engine_call(self, discarded_, choice_, message_):
        if message_.startswith("Ron"):
            return "Ron", []
        else:
            return "Skip", []


    def inform_dora(self, tilecode_):
        self.doras.append(tilecode_)
        self.inform_dora_additional(tilecode_)


    def inform_dora_additional(self, tilecode_):
        pass



    def inform_newdora(self, tilecode_):
        self.doras.append(tilecode_)

    def others_discard(self, relid_, discarded_, tsumogiri_=False, riichi_=False, caller_relid_=-1,
                       exposed_=[]):
        self.ponds[relid_].append((discarded_, tsumogiri_, riichi_, caller_relid_))
        # 鳴いた人がいる場合、その処理を追加
        if caller_relid_ >= 0:
            self.exposes[caller_relid_].append(exposed_)

    def engine_discard(self, draw_pai_, riichi_=[], tsumo_=False, kong_=[]):
        return draw_pai_, riichi_, True


    def engine_chow(self):
        pass

    def engine_pong(self):
        pass

    def engine_kong(self):
        pass

    def sort_hand(self):
        def tile_index(tilecode):
            index = 0
            index += int(tilecode[0])
            # 赤なら5扱い
            if tilecode[0] == "0":
                index += 5

            if tilecode[1] == "p":
                index += 10
            elif tilecode[1] == "s":
                index += 20
            elif tilecode[1] == "z":
                index += 30

            return index

        self.hand.sort(key=tile_index)



class RemoteJanshi(Janshi):

    connection = None

    def __init__(self, conn):
        super.__init__()
        self.connection = VirtualClient(conn)


    def engine_discard(self, draw_pai_, riichi_=[], tsumo_=False, kong_=[]):
        message = "DRAW {}".format(draw_pai_)

        if len(riichi_):
            message += " RIICHI({})".format(",".join(riichi_))

        if tsumo_:
            message += ",TSUMO"

        self.connection.send_message(message)
        ret = self.connection.receive_until(["DISCARD", "TSUMO", "KAN"])

        if ret.startswith("DISCARD"):
            parts = ret.split(" ")
            return "Discard", parts[1], parts[2]


    def inform_dora_additional(self, tilecode_):
        message = "DORA {}".format(tilecode_)
        self.connection.send_message(message)



class VirtualClient:
    def __init__(self, conn_):
        self.connection = conn_


    def send_message(self, message_):
        self.connection.send(message_)

    # commandと一致するのが出てくるまで
    def receive_until(self, commands_, timeout_s_=20):
        self.connection.settimeout(timeout_s_)
        try:
            while True:
                text = self.connection.recv(4096).decode()
                lines = text.split("\n")
                for line in lines:
                    parts = line.split(" ")
                    if parts[0] in commands_:
                        return line.strip()
        except Exception as e:
            print(e)
        finally:
            self.connection.settimeout(None)

class KoritsuChu(Janshi):
    def engine_discard(self, draw_pai_, riichi_=False, tsumo_=False, kong_=[]):
        # ツモ可能であれば、すぐにあがる
        if tsumo_:
            return "Tsumo", False, False

        if self.riichi_flag:
            return "Discard", draw_pai_, True

        # 立直可能であれば立直する
        if riichi_:
            command = "Riichi"
        else:
            command = "Discard"

        self.sort_hand()
        # 背理を使って最善を出す
        hairi = LisJongUtils.logic_tile("".join(self.hand)+draw_pai_)
        maxuke = 0
        maxri = ""
        for ri in hairi:
            if hairi[ri] >= maxuke:
                maxri = ri
                maxuke = hairi[ri]

        # 5を切ろうとしてなかったらをキル
        if maxri not in self.hand and maxri != draw_pai_:
            maxri = maxri.replace("5", "0")

        print("".join(self.hand) + "," + draw_pai_)
        print("Discard {0}".format(maxri))
        return command, maxri, False


class Human(Janshi):

    def __init__(self, name_, initial_score_=25000):
        super().__init__(name_, initial_score_)
        self.poncount = 0

    def engine_discard(self, draw_pai_, riichi_=[], tsumo_=False, kong_=[]):
        # 自分の手配を表示
        self.sort_hand()
        # 選択し表示
        line = "".join(self.hand) + "," + draw_pai_
        # リーチ可能なら表示
        if len(riichi_) > 0:
            line += ",riichi({0})".format(",".join(riichi_))
        if tsumo_:
            line += ",Tsumo"
        if len(kong_) > 0:
            for kong_tile in kong_:
                line += ",kong_{0}".format(kong_tile)
        print(line)

        tilecode = input()
        #tilecode = ""

        if tilecode == "Tsumo":
            waits = LisJongUtils.machi("".join(self.hand), [])
            # 当たっているものを
            for wait in waits:
                if draw_pai_ in wait[1]:
                    # 当たっていればそれから点数計算
                    agari = LisJongUtils.calculate_score_one(wait[0], [], draw_pai_,
                                                             True, True, "1z", "1z", True, False, False, False,
                                                             ["3m"], ["4m"], False)
                    print(agari)
            return "Tsumo", False, False

        # 立直可能であれば立直する
        if riichi_:
            command = "Riichi"
        else:
            command = "Discard"

        if tilecode == "":
            return command, draw_pai_, True
        if tilecode != draw_pai_:
            return command, tilecode, False
        else:
            return command, tilecode, True


    def engine_call(self, discarded_, choice_, message_):
        #泣きがあったことを示す
        print("Discarded {}".format(discarded_))
        print(choice_)

        command = input()

        if command == "Pon":
            return "Pon", choice_["Pon"][0]
        elif command == "Chii":
            return "Chii", choice_["Chii"][0]
        # 椪かちーかだけ
        return "Skip", []



class LisJongServer():
    def __init__(self):
        self.clients = []

    def start(self, port_, count_=4):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), port_))
        s.listen(5)

        #接続待機
        while True:
            try:
                conn, addr = s.accept()
            except KeyboardInterrupt:
                s.close()
                exit()
                break
            #クライアントの追加
            self.clients.append((conn, addr))

            # HELLOを送信するかチェックして、それを受け取ったらよし

            # 読み込みたい気を開始する
            thread = threading.Thread(target=self.hello, args=(conn, addr), daemon=True)
            thread.start()

            #４人揃ったら待機終了
            if len(self.clients) >= count_:
                break


    def hello(self, connection_, address_):
        while True:
            try:
                # クライアント側から受信する
                res = connection_.recv(4096)
                message = res.decode().strip()
                if message.startswith("HELLO"):
                    parts = message.split(" ")
                    # 名前のセット
                    name = parts[1]

                    connection_.send("ACCEPT {}".format(name).encode("UTF-8"))

                    return
            except Exception as e:
                print(e)
                break


    def receiver(self, connection_, address_):
        while True:
            try:
                # クライアント側から受信する
                res = connection_.recv(4096)
                for value in self.clients:
                    if value[1][0] == address_[0] and value[1][1] == address_[1]:
                        print("クライアント{}:{}から{}というメッセージを受信完了".format(value[1][0], value[1][1], res))
                    else:
                        value[0].send(
                            "クライアント{}:{}から{}を受信".format(value[1][0], value[1][1], res.decode()).encode("UTF-8"))
                        pass
            except Exception as e:
                print(e)
                break


class Table():

    def __init__(self):
        # 現在の場
        self.round = 0
        # 現在の局数
        self.game = 0
        # 現在の本場
        self.extra = 0


    def start_match(self, pnames_, settings_):

        # ログの記録先
        self.logger = mjlogger.DennoJson("sample.json", pnames_, "LisJong対戦開幕戦")
        self.loginfo = {}

        # サーバー目線の情報の格納場所
        self.plinfo = PlayersInfo(pnames_)

        # サーバー目線のプレイヤー 情報は自主管理
        self.players = []
        for i in range(4):
            self.players.append(KoritsuChu(pnames_[i]))

        # 半荘か東風戦か、
        self.round_max = 1

        # 点数設計
        initial_score = 25000

        # 超えるべき点数
        self.score_threshold = 30000

        # 初期化
        self.deposit = 0

        # 名前設定
        self.players = [KoritsuChu("keyboard"), KoritsuChu("1"), KoritsuChu("2"), KoritsuChu("3")]

        while True:
            lastgame = self.start_game()
            self.logger.write_game(**self.loginfo)

            if not lastgame:
                break


        # 最終的な結果作成
        result = {
            "score":[self.players[plid].score for plid in range(4)],
            "rank":[1,2,3,4],
            "point":[0,0,0,0]
        }
        self.logger.end_match(**result)
        self.logger.output()



    def start_game(self):

        self.loginfo = {}

        self.called_discard_flag = False

        # 灰山生成
        tilepilestr, hashstr = self.create_tilepile()

        self.wall = []
        for i in range(TILE_TOTAL):
            self.wall.append(tilepilestr[2 * i:2 * i + 2])
        #配牌
        starting_hands = ["", "", "", ""]
        # 4つずうつ3回
        for i in range(3):
            for plid in range(PLAYER_COUNT):
                starting_hands[plid] += "".join(self.wall[i * 16 + plid * 4:i * 16 + plid * 4 + 4])
        # 1つずつ
        chon_start = 12 * 4
        for p in range(PLAYER_COUNT):
            starting_hands[p] += self.wall[chon_start + p]

        for q in range(PLAYER_COUNT):
            kijun = (q + self.game) % 4
            self.players[kijun].newgame()
            self.players[kijun].initial_draw(starting_hands[q])
            self.plinfo.hands[kijun] = LisJongUtils.disintegrate_hand(starting_hands[q])


        #dora 山全体から-5が表、そこから裏、新どら、新どら裏、とマイナスに続く
        self.dora = []
        self.underneath_dora = []
        self.dora.append(LisJongUtils.dora_from_indicator(self.wall[POSITION_DORA]))
        self.underneath_dora.append(LisJongUtils.dora_from_indicator(self.wall[POSITION_DORA - 1]))
        for p in range(PLAYER_COUNT):
            self.players[p].inform_dora(self.dora[0])


        self.next_tsumo_id = 13 * 4
        self.kong_count = 0

        gameresult = ""

        turnplayer = self.game

        # ログ-開始時点の　供託、本場、点数、配牌を記録する
        self.loginfo["extra"] = self.extra
        self.loginfo["round"] = self.round
        self.loginfo["game"] = self.game
        self.loginfo["deposit"] = self.deposit
        self.loginfo["initial_score"] = [self.players[plid].score for plid in range(4)]
        self.loginfo["initial_hand"] = ["".join(self.players[plid].hand) for plid in range(4)]
        self.loginfo["dora1_indicator"] = self.wall[POSITION_DORA]
        self.loginfo["dora1"] = LisJongUtils.dora_from_indicator(self.wall[POSITION_DORA])
        self.loginfo["actions"] = []

        while self.next_tsumo_id <= TILE_TOTAL - DEADWALL_COUNT - self.kong_count:
            # 現在のターンプレイヤーに引かせる
            # リーチ判断
            # shanten0, -1ならリーチあり
            if not self.called_discard_flag:
                drawtile_id = self.wall[self.next_tsumo_id]
                fullhand = self.plinfo.hands[turnplayer] + [drawtile_id]
                # ドローが確定する
                self.loginfo["actions"].append({"action": "draw", "plid": turnplayer, "tile": drawtile_id})

                # shantenへいれる
                shanten_triple = LisJongUtils.shanten("".join(fullhand).replace('0', '5'))
                # shanten=0なら立直宣言はいも教える
                fullhand_copy = []
                riichi_list = []
                if 0 in shanten_triple or -1 in shanten_triple:
                    for tile in fullhand:
                        fullhand_copy.append(tile)
                    # 手札の1種類ずつを外してみて、待ちが発生すればそれに従う
                    for tile in fullhand:
                        if not tile in riichi_list:
                            fullhand_copy.remove(tile)
                            machiresult = LisJongUtils.machi("".join(fullhand_copy), [])
                            if len(machiresult) > 0:
                                riichi_list.append(tile)
                            fullhand_copy.append(tile)

                tsumo_result = self.players[turnplayer].draw(drawtile_id, riichi_list, shanten_triple[0] < 0)
                # ログ保存
                self.loginfo["actions"].append({"action": "discard", "plid": turnplayer, "tile": tsumo_result[1],
                                                "riichi": tsumo_result[0] == "Riichi", "tsumogiri": tsumo_result[2]})

            else:
                # 自摸なし
                drawtile_id = ""
                fullhand = self.plinfo.hands[turnplayer]
                tsumo_result = self.players[turnplayer].draw_called()


            # 0commnad, 1hai, 2tsumogiriflag
            if tsumo_result[0] == "Discard" or tsumo_result[0] == "Riichi":
                # 手札の更新
                if not tsumo_result[2]:
                    try:
                        self.plinfo.hands[turnplayer].remove(tsumo_result[1])
                        self.plinfo.hands[turnplayer].append(drawtile_id)
                    except:
                        print(self.plinfo)

                # ロンがあるかどうかを見る
                callret = [[],[],[],[]]
                for plid in range(4):
                    callmessage = ""
                    if plid != turnplayer:
                        machiresult = LisJongUtils.machi("".join(self.plinfo.hands[plid]), self.plinfo.exposes[plid])
                        for waits in machiresult:
                            # TODO 本来はフリテンチェック、役ありチェックが必要
                            if str(tsumo_result[1]) in waits[1]:
                                callmessage += "Ron,"
                        # 鳴く人がいれば、turnplayerから逆順に確認する
                        if self.next_tsumo_id + self.kong_count < TILE_TOTAL - DEADWALL_COUNT:
                            calla = LisJongUtils.check_call("".join(self.plinfo.hands[plid]), tsumo_result[1])
                            # 次のプレイヤーのみチー可能
                            if plid == (turnplayer + 1) % 4 and len(calla["Chii"]) > 0:
                                for chiiable in calla["Chii"]:
                                    callmessage += "Chii({}),".format(",".join(chiiable))
                            if len(calla["Pon"]) > 0:
                                callmessage += "Pon({}),".format(",".join(calla["Pon"][0]))
                            if len(calla["Kan"]) > 0:
                                callmessage += "Kan({})".format(",".join(calla["Kan"][0]))

                            # messageがあれば送信
                            if len(callmessage) > 0:
                                callret[plid] = self.players[plid].call(tsumo_result[1], calla, callmessage)

                # 次のプレイヤーから見て、ロンがあれば終了
                for offset in range(1, 4, 1):
                    if isinstance(callret[(turnplayer + offset) % 4], tuple) and callret[(turnplayer + offset) % 4][0] == "Ron":
                        # その人の論として終了 ふりこみ、あがり
                        gameresult += "Ron({},{}),".format(turnplayer, (turnplayer + offset) % 4)
                if len(gameresult) > 0:
                    break

                # ロンがない時点で、立直は成立する, そうでなく自摸ぎったなら、その人の一発フラグを消す
                if tsumo_result[0] == "Riichi":
                    self.players[turnplayer].riichi_flag = True
                    self.players[turnplayer].oneshot_flag = True
                    self.players[turnplayer].score -= 1000
                    self.deposit += 1
                else:
                    self.players[turnplayer].oneshot_flag = False

                # ロンがなければ、次はポンを調べる
                called = ""
                for offset in range(3):
                    if isinstance(callret[(turnplayer - offset - 1) % 4], tuple) and callret[(turnplayer - offset - 1) % 4][0] != "Skip":
                        # そのアクションを実行する
                        # 捨てはいを確定させ、鳴かれたことを記録する
                        # 鳴いた灰
                        caller = (turnplayer - offset - 1) % 4
                        called = LisJongUtils.arrange_tile(tsumo_result[1] + "".join(callret[(turnplayer - offset - 1) % 4][1]))
                        called = "{" + called + "}"

                        self.plinfo.exposes[caller].append(called)
                        for p in range(4):
                            self.players[p].inform_call((turnplayer - p) % 4, tsumo_result[1],
                                                        (caller - p) % 4, callret[caller][0], called)

                        # 手配からさらしたぶんを削除
                        for placeid in range(len(callret[caller][1])):
                            self.plinfo.hands[caller].remove(callret[caller][1][placeid])

                # 何もなしに捨てはいが確定している???
                for qlid in range(4):
                    self.players[qlid].others_discard((turnplayer - qlid) % 4, tsumo_result[1], tsumo_result[2], tsumo_result[0] == "Riichi",
                                                      -1 if len(called) == 0 else (caller - qlid) % 4, called)


                # 泣きがあれば、自摸なしにその人のターンとする
                if len(called) > 0:
                    turnplayer = caller

                else:
                    turnplayer = (turnplayer + 1) % 4
                    self.next_tsumo_id += 1



            elif tsumo_result[0] == "Kong":
                pass
            elif tsumo_result[0] == "Tsumo":
                gameresult = "Tsumo"
                break

            # 残り枚数がないなら、荒れ牌流局とする
            if self.next_tsumo_id >= (TILE_TOTAL - DEADWALL_COUNT - self.kong_count):
                gameresult = "Goulash"
                break


        # gameresultによる分岐
        if gameresult.startswith("Tsumo"):
            # 点数計算をする
            score = LisJongUtils.calculate_score("".join(self.players[turnplayer].hand),
                                                 self.players[turnplayer].exposes[0],
                                                 drawtile_id, True, turnplayer == self.game,
                                                 WIND_TABLE[self.game], WIND_TABLE[turnplayer],
                                                 self.players[turnplayer].riichi_flag,
                                                 self.players[turnplayer].oneshot_flag, self.next_tsumo_id == TILE_TOTAL - DEADWALL_COUNT - self.kong_count,
                                                 False, self.dora, self.underneath_dora)

            print(score)
            #TODO 結果を知らせる

            #点数の移動
            scorediff = [0] * 4
            if turnplayer == self.game:
                # 親ならall部分除いて移動
                diffpoint = int(score[0][0:-3])
                # 本場の分を加算する
                diffpoint += self.extra * 100
                for plid in range(4):
                    if plid != turnplayer:
                        scorediff[plid] = - diffpoint
                        self.players[plid].score -= diffpoint
                    else:
                        scorediff[plid] = 3 * diffpoint + self.deposit * 1000
                        self.players[plid].score += scorediff[plid]
            else:
                diffpoint_child = int(score[0].split("-")[0]) + self.extra * 100
                diffpoint_dealer = int(score[0].split("-")[1]) + self.extra * 100
                for plid in range(4):
                    if plid == turnplayer:
                        scorediff[plid] = 2*diffpoint_child + diffpoint_dealer + self.deposit*1000
                        self.players[plid].score += 2*diffpoint_child + diffpoint_dealer
                    elif plid == self.game:
                        scorediff[plid] = - diffpoint_dealer
                        self.players[plid].score -= diffpoint_dealer
                    else:
                        scorediff[plid] = - diffpoint_child
                        self.players[plid].score -= diffpoint_child

            self.players[turnplayer].score += 1000*self.deposit
            self.deposit = 0

            # 上がりのログ保存
            self.loginfo["win"] = {
                "winby":"Tsumo",
                "winner":turnplayer,
                "hand":"".join(self.players[turnplayer].hand),"exposed":self.players[turnplayer].exposes[0],
                "winning_tile":drawtile_id,
                "score":score
            }

            self.loginfo["score_diff"] = scorediff


            for plid in range(4):
                print(self.players[plid].score)

            if turnplayer == self.game:
                return self.renchan()
            else:
                return self.next_game()

        elif gameresult.startswith("Ron"):
            # 点数計算
            payer_id = int(gameresult[4])
            winner_id = int(gameresult[6])
            score = LisJongUtils.calculate_score("".join(self.players[winner_id].hand),
                                                 self.players[winner_id].exposes[0],
                                                 tsumo_result[1], False, winner_id == self.game,
                                                 WIND_TABLE[self.game], WIND_TABLE[winner_id],
                                                 self.players[winner_id].riichi_flag,
                                                self.players[winner_id].oneshot_flag, self.next_tsumo_id == TILE_TOTAL - DEADWALL_COUNT - self.kong_count,
                                                 False, self.dora, self.underneath_dora)

            print(score)
            diffpoint = int(score[0]) + self.extra * 300
            self.players[payer_id].score -= diffpoint
            self.players[winner_id].score += diffpoint

            self.players[winner_id].score += 1000*self.deposit

            # 上がりのログ保存
            self.loginfo["win"] = {
                "winby":"Ron",
                "winner":winner_id, "payer":payer_id,
                "hand":"".join(self.players[winner_id].hand),"exposed":self.players[winner_id].exposes[0],
                "winning_tile":tsumo_result[1],
                "score":score
            }
            # 展望移動
            scorediff = [0] * 4
            for plid in range(4):
                if plid == winner_id:
                    scorediff[plid] = diffpoint + self.deposit*1000
                elif plid == payer_id:
                    scorediff[plid] = - diffpoint

            self.loginfo["score_diff"] = scorediff

            # 次の曲に向けての初期化処理　自摸の場合と合わせるべき
            # TODO
            self.deposit = 0

            for plid in range(4):
                print(self.players[plid].score)

            if winner_id == self.game:
                return self.renchan()
            else:
                return self.next_game()

        elif gameresult.startswith("Goulash"):
            # 聴牌している人とTendaいしていない人を分ける
            tempaier_list = []
            noten_list = []
            for plid in range(4):
                shanten_triple = LisJongUtils.shanten("".join(self.players[plid].hand))
                if 0 in shanten_triple:
                    tempaier_list.append(plid)
                else:
                    noten_list.append(plid)

            #TODO 聴牌者の通知
            print("Tempai:{}".format(tempaier_list))
            print("Noten:{}".format(noten_list))

            # 点数のやり取り
            scorediff = [0] * 4
            if len(tempaier_list) > 0 and len(tempaier_list) < 4:
                for tempaier in tempaier_list:
                    self.players[tempaier].score += int(TEMPAI_ADVANTAGE / len(tempaier_list))
                for notener in noten_list:
                    self.players[notener].score -= int(TEMPAI_ADVANTAGE / len(noten_list))
                for plid in range(4):
                    if plid in tempaier_list:
                        scorediff[plid] = int(TEMPAI_ADVANTAGE / len(tempaier_list))
                    else:
                        scorediff[plid] = - int(TEMPAI_ADVANTAGE / len(noten_list))

            # 親が聴牌して, かつ１位いれば、連荘、そうでないなら流れる
            # TODO 聴牌やメアリ

            if self.game in tempaier_list:
                self.extra += 1
                # 継続フラグは得点条件のみ
            else:
                self.extra += 1
                self.next_game()


            self.loginfo["draw"] = {
                "name":"Goulash",
                "hand":["".join(self.players[qlid].hand) for qlid in range(4)]
            }
            self.loginfo["score_diff"] = scorediff

            return True


    def check_continue_byscore(self):
        # 箱下がいれば終了
        for p in range(4):
            if self.players[p].score < 0:
                return False

        # トップが異常なら終了
        okagoe_flag = False
        for plid in range(4):
            if self.players[plid].score > self.score_threshold:
                okagoe_flag = True

        return okagoe_flag


    # next gameがあうときはTrueを返す
    def next_game(self):
        # 本場リセット
        self.extra = 0

        # 箱下がいれば終了
        for p in range(4):
            if self.players[p].score < 0:
                return False

        # オーラスの場合
        if self.game == 3 and self.round >= self.round_max:
            # ゲーム終了条件を満たしているかチェック
            # 誰かが超えているか
            okagoe_flag = False
            for plid in range(4):
                if self.players[plid].score > self.score_threshold:
                    okagoe_flag = True
                    break
            if okagoe_flag:
                return False
            else:
                self.game =1
                self.round += 1
                return True
        else:
            if self.game == 3:
                self.game = 0
                self.round += 1
            else:
                self.game += 1
            return True


    def renchan(self):
        self.extra += 1
        return True



    #
    # 返り値：山コード　ハッシュ
    def create_tilepile(self):
        #4種あるもの
        hai4list = ["1m","2m","3m","4m","6m","7m","8m","9m",
                    "1p", "2p", "3p", "4p", "6p", "7p", "8p", "9p",
                    "1s", "2s", "3s", "4s", "6s", "7s", "8s", "9s",
                    "1z", "2z", "3z", "4z", "5z", "6z", "7z"]
        #3種あるもの
        hai3list = ["5m", "5p", "5s"]
        #1個あるもの
        hai1list = ["0m", "0p", "0s"]
        #一つのリストを作る
        tile_pile = []
        for tilename in hai4list:
            for i in range(4):
                tile_pile.append(tilename)
        for tilename in hai3list:
            for i in range(3):
                tile_pile.append(tilename)
        for tilename in hai1list:
            tile_pile.append(tilename)

        #並び替え
        #シードは日付ミリ秒
        epochtime = int(time.time()*1000 % 2**31)
        self.shuffle(tile_pile, epochtime)
        #メモリ使用率から再度シャッフル
        memory = (psutil.virtual_memory().total + psutil.virtual_memory().available) % 2**31
        self.shuffle(tile_pile, memory)

        #中身を文字列としてつなぎ合わせる
        piletile_str = "".join(tile_pile) + "_" + str(datetime.datetime.now())
        return piletile_str, hashlib.sha512(piletile_str.encode("utf-8")).hexdigest()

    def shuffle(self, tilepile_, seed_):
        np.random.seed(seed_)
        for i in range(TILE_TOTAL):
            swap_target = np.random.randint(i, TILE_TOTAL)
            temp = tilepile_[i]
            tilepile_[i] = tilepile_[swap_target]
            tilepile_[swap_target] = temp
        return tilepile_



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    taku = Table()
    tilepile, hash = taku.create_tilepile()
    print(tilepile)
    print(hash)

    taku.start_match(["1", "2", "3", "4"], {})

#    serv = LisJongServer()
#    serv.start(80)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
