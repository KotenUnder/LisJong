# This is a sample Python script.
import datetime
import hashlib
import numpy as np
import time
import psutil
import socket
import threading
import LisJongUtils
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


TILE_TOTAL = 4 * (9+9+9+7)
PLAYER_COUNT = 4
POSITION_DORA = TILE_TOTAL - 5

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


class Janshi():
    def __init__(self, name_, initial_score_=25000):
        self.name = name_
        self.score = initial_score_
        self.hand = []
        self.river = []


    def initial_draw(self, initial13str_):
        for i in range(13):
            self.hand.append(initial13str_[i*2:i*2+2])

    # キル杯を返す
    def draw(self, draw_pai_, riichi_=False, tsumo_=False, kong_=[]):
        discard_tile, tsumogiri_flag = self.engine_discard(draw_pai_, riichi_, tsumo_, kong_)
        if not tsumogiri_flag:
            if discard_tile in self.hand:
                discard_id = self.hand.index(discard_tile)
                self.hand[discard_id] = draw_pai_

        return discard_tile, tsumogiri_flag

    def engine_discard(self, draw_pai_, riichi_=False, tsumo_=False, kong_=[]):
        return draw_pai_, True

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




class Human(Janshi):

    def engine_discard(self, draw_pai_, riichi_=False, tsumo_=False, kong_=[]):
        # 自分の手配を表示
        self.sort_hand()
        # 選択し表示
        line = "".join(self.hand) + "," + draw_pai_
        # リーチ可能なら表示
        if riichi_:
            line += ",riichi"
        if tsumo_:
            line += ",Tsumo"
        if len(kong_) > 0:
            for kong_tile in kong_:
                line += ",kong_{0}".format(kong_tile)
        print(line)

        tilecode = input()
        if tilecode == draw_pai_:
            return draw_pai_, True
        else:
            return tilecode, False

class LisJongServer():
    def __init__(self):
        self.clients = []

    def start(self, port_):
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
            # 読み込みたい気を開始する
            thread = threading.Thread(target=self.receiver, args=(conn, addr), daemon=True)

            #４人揃ったら待機終了
            if len(self.clients) >= 4:
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
                print(e);
                break;

class Table():

    def __init__(self):
    # 現在の局数
        self.round = 1
        self.game = 1
        self.extra = 0



    def start_game(self):
        # 名前設定
        self.players = [Human("keyboard"), Janshi("1"), Janshi("2"), Janshi("3")]

        # 灰山生成
        tilepilestr, hashstr = self.create_tilepile()

        self.pile = []
        for i in range(TILE_TOTAL):
            self.pile.append(tilepilestr[2*i:2*i+2])
        #配牌
        starting_hands = ["", "", "", ""]
        # 4つずうつ3回
        for i in range(3):
            for p in range(PLAYER_COUNT):
                starting_hands[p] += "".join(self.pile[i*16+p*4:i*16+p*4+4])
        # 1つずつ
        for p in range(PLAYER_COUNT):
            chon_start = 12 * 4
            starting_hands[p] += self.pile[chon_start+p]

        for p in range(PLAYER_COUNT):
            self.players[p].initial_draw(starting_hands[p])

        #dora
        self.dora = []
        self.dora.append(self.pile[POSITION_DORA])

        self.next_tsumo_id = 48
        self.kong_count = 0

        turnplayer = 0
        while self.next_tsumo_id <= 122:
            # 現在のターンプレイヤーに引かせる
            # リーチ判断
            # shanten0, -1ならリーチあり
            drawtile_id = self.pile[self.next_tsumo_id]
            fullhand = self.players[turnplayer].hand + [drawtile_id]
            # shantenへいれる
            shanten_triple = LisJongUtils.shanten("".join(fullhand).replace('0', '5'))
            self.players[turnplayer].draw(drawtile_id, shanten_triple[0] < 1, shanten_triple[0] < 0)

            self.next_tsumo_id += 1
            turnplayer = (turnplayer + 1) % 4


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
    print_hi('PyCharm')
    taku = Table()
    tilepile, hash = taku.create_tilepile()
    print(tilepile)
    print(hash)

    taku.start_game()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/