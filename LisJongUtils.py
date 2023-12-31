
import re

#return
# fu
# faan
# yaku-list
# points

SCORE_CHILD_MANGAN = 2000
SCORE_DEALER_MANGAN = 4000

SCORETABE_CHILD = [
    [],
    [[(200, 400), (400, 800), (800, 1600), (1600, 3200)], [800, 1600, 3200, 6400]],
    [[(200, 400), (400, 700), (700, 1300), (1300, 2600)], [700, 1300, 2600, 5200]],
    [[(300, 500), (500, 1000), (1000, 2000), (2000, 3900)],[1000, 2000, 3900, 7700]],
    [[(400, 700), (700, 1300), (1300, 2600), (2000, 4000)], [1300, 2600, 5200, 8000]],
    [[(400, 800), (800, 1600), (1600, 3200), (2000, 4000)], [1600, 3200, 6400, 8000]],
    [[(500, 1000), (1000, 2000), (2000, 3900), (2000, 4000)], [2000, 3900, 7700, 8000]],
    [[(600, 1200), (1200, 2300), (2000, 4000), (2000, 4000)], [2300, 4500, 8000, 8000]]
]

# 確定頭、確定メンツ、頭候補、面子候補
TABLE_CANDIDATOR_COMBINATION = [
    [[0,0,0,0]],
    [[0,0,1,0]],
    [[1,0,0,0], [0,0,0,1]],
    [[0,1,0,0]],
    [[1,0,0,1], [0,1,1,0]],
    [[1,1,0,0], [0,1,0,1]],
    [[0,2,0,0]],
    [[1,1,0,1], [0,2,1,0]],
    [[1,2,0,0], [0,2,0,1]],
    [[0,3,0,0]],
    [[1, 2, 0, 1], [0, 3, 1, 0]],
    [[1, 3, 0, 0], [0, 3, 0, 1]],
    [[0, 4, 0, 0]],
    [[1,3,0,1], [0,4,1,0]]
]

meldstable = {}
meldsfile = open("MeldsTable.txt", "r")
meldsfile.readline()
for line in meldsfile:
    parts = line.split("\t")
    meldstable[parts[0]] = parts[1].strip()


def calculate_fu(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_):
    fu = 20
    #面前論で10
    if len(exposedstrlist_) == 0 and not winbyself_:
        fu += 10

    #上がり方につく符
    for elem in closedhandstr_:
        if elem[0] != "(" and elem[0] != "[" and elem[0] != "{":
            #頭なら2
            if len(elem) == 2:
                fu += 2
            #カンチャン、ペンちゃんなら2
            elif int(elem[0]) == int(elem[2]) - 2 or (elem[0] == "1" and elem[2] == "2") or (elem[0] == "8" and elem[2] == "9"):
                fu += 2

    #合体
    melded = meld(closedhandstr_, exposedstrlist_, winningpai_)

    for trip in melded:
        if trip.startswith("["):
            #自風、場風ならそれぞれ+2
            if trip[1:3] == prevailingwind_:
                fu += 2
            if trip[1:3] == ownwind_:
                fu += 2
        elif trip.startswith("("):
            #順子ならなし
            nowp = 0
            if trip[1:3] != trip[3:5]:
                fu += 0
            #3つ
            else:
                if paicheck_simple(trip[1:3]):
                    nowp = 4
                else:
                    nowp = 8
                #カンなら倍
                if len(trip) == 10:
                    nowp *= 2
                fu += nowp
        elif trip.startswith("{"):
            #順子ならなし
            nowp = 0
            if trip[1:3] != trip[3:5]:
                fu += 0
            #3つ
            else:
                if paicheck_simple(trip[1:3]):
                    nowp = 2
                else:
                    nowp = 4
                #カンなら倍
                if len(trip) == 10:
                    nowp *= 2
                fu += nowp

    #特殊：平和自摸=20
    if winbyself_ and fu > 20:
        fu += 2

    return fu


def calculate_score_one(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_, riichi_, oneshot_, last_, robbing_kong_, doras_, u_doras_,
                        heaven_=False):
    #
    yaku_list = []

    # 赤ドラ ０－５の差し替え
    rdora_count = 0
    closed2 = []
    exposed2 = []
    for trip in closedhandstr_:
        rdora_count += trip.count("0")
        closed2.append(trip.replace("0", "5"))
    for trip in exposedstrlist_:
        rdora_count += trip.count("0")
        exposed2.append(trip.replace("0", "5"))
    rdora_count += winningpai_.count("0")

    closedhandstr_ = closed2
    exposedstrlist_ = exposed2
    winningpai_ = winningpai_.replace("0", "5")


    # 最初に役満チェック　役満成立していたらそこで点数計算終了
    if yakucheck_big4wind(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Big 4 Winds")
    elif yakucheck_little4wind(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Little 4 Winds")

    if yakucheck_allterminal(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("All Terminals")

    if yakucheck_4quads(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("4 Quads")

    ninegates = yakucheck_ninegates(closedhandstr_, exposedstrlist_, winningpai_)
    if ninegates == 1:
        yaku_list.append("Nine Gates")
    elif ninegates == 2:
        yaku_list.append("Nine Gates (nine waits)")

    if yakucheck_big3dragon(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Big 3 Dragons")

    suanko = yakucheck_4conceal(closedhandstr_, exposedstrlist_, winningpai_, winbyself_)
    if suanko == 1:
        yaku_list.append("4 Concealed Triplets")
    elif suanko == 2:
        yaku_list.append("4 Concealed Triplets (single wait)")

    if heaven_ and is_dealer_:
        yaku_list.append("Heavenly Hand")
    elif heaven_ and not is_dealer_:
        yaku_list.append("Earth Hand")

    # 役満が１つでもあれば、役満ありとして計算する
    if len(yaku_list) > 0:
        limits = count_limit(yaku_list)
        point, comment = getpoints("Limit"+str(limits), "", is_dealer_, winbyself_)
        return point, comment, yaku_list



    # 役満がない普通の場合
    # 立直していたら追加
    if riichi_ == 1:
        yaku_list.append("Ready")
    elif riichi_ == 2:
        yaku_list.append("Ready 2")

    # 一発の追加
    if oneshot_:
        yaku_list.append("One Shot")

    # 面前自摸
    if len(exposedstrlist_) == 0 and winbyself_:
        yaku_list.append("Pure Self-Pick")

    # 海底　ホー艇
    if last_:
        if winbyself_:
            yaku_list.append("Last Pick")
        else:
            yaku_list.append("Last Discard")


    # ふけいさん
    fu = calculate_fu(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_)

    # 平和の判定 tsumo20 or ron30
    if len(exposedstrlist_) == 0 and ((winbyself_ and fu == 20) or (not winbyself_ and fu == 30)):
        yaku_list.append("Peace")

    # タンヤオの判定
    if yakucheck_simples(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("All Simples")

    # 3色の判定
    if yakucheck_3color_chow(closedhandstr_, exposedstrlist_, winningpai_):
        if len(exposedstrlist_) == 0:
            yaku_list.append("3 Color Straights")
        else:
            yaku_list.append("3 Color Straights (open)")
    if yakucheck_3color_pong(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("3 Color Triplets")

    # 3 anko
    if yakucheck_3conceal(closedhandstr_, exposedstrlist_, winningpai_, winbyself_):
        yaku_list.append("3 Concealed Triplets")

    #3かん
    if yakucheck_3quads(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("3 Quads")

    # 1peko, 2peko
    if yakucheck_1peko(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("1Peko")
    elif yakucheck_2peko(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("2Peko")

    # 役牌
    yakuhais = yakucheck_yakuhai(closedhandstr_, exposedstrlist_, winningpai_, prevailingwind_, ownwind_)
    if len(yakuhais) > 0:
        yaku_list.extend(yakuhais)

    # ちゃん田、うんちゃん
    if yakucheck_junchan(closedhandstr_, exposedstrlist_, winningpai_):
        if len(exposedstrlist_) > 0:
            yaku_list.append("Junchan (open)")
        else:
            yaku_list.append("Junchan")
    elif yakucheck_chanta(closedhandstr_, exposedstrlist_, winningpai_):
        if len(exposedstrlist_) > 0:
            yaku_list.append("Chanta (open)")
        else:
            yaku_list.append("Chanta")

    #ほんいつけい
    if yakucheck_semiflush(closedhandstr_, exposedstrlist_, winningpai_):
        if len(exposedstrlist_) > 0:
            yaku_list.append("Semi-Flush (open)")
        else:
            yaku_list.append("Semi-Flush")
    elif yakucheck_flush(closedhandstr_, exposedstrlist_, winningpai_):
        if len(exposedstrlist_) > 0:
            yaku_list.append("Flush (open)")
        else:
            yaku_list.append("Flush")

    # 一気通貫
    if yakucheck_straight(closedhandstr_, exposedstrlist_, winningpai_):
        if len(exposedstrlist_) > 0:
            yaku_list.append("Straight (open)")
        else:
            yaku_list.append("Straight")

    # といとい
    if yakucheck_toitoi(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("All Triplets")

    han = count_han(yaku_list)

    # どらを数える

    serial = serialize(closedhandstr_, exposedstrlist_, winningpai_)
    dora_count = 0
    udora_count = 0
    for dora in doras_:
        for i in range(int(len(serial)/2)):
            needlepai = serial[i*2:i*2+2]
            if needlepai == dora:
                dora_count += 1
    for dora in u_doras_:
        for i in range(int(len(serial) / 2)):
            needlepai = serial[i * 2:i * 2 + 2]
            if needlepai == dora:
                udora_count += 1

    han += (dora_count + udora_count + rdora_count)
    if dora_count > 0:
        yaku_list.append("Dora {0}".format(dora_count))
    if udora_count > 0:
        yaku_list.append("Underneath Dora {0}".format(udora_count))
    if rdora_count > 0:
        yaku_list.append("Red Dora {0}".format(rdora_count))

    point, comment = getpoints(fu, han, is_dealer_, winbyself_)

    # 返すべきものが多いのでjson形式とする
    result = {
        "comment":comment
    }

    return point, comment, yaku_list


def count_han(yakulist_):
    handict = {
        "Ready":1,
        "Ready 2":2,
        "Pure Self-Pick":1,
        "One Shot":1,
        "Last Pick":1,
        "Last Discard":1,
        "1Peko":1,
        "All Simples":1,
        "Peace":1,
        "Prevailing Wind":1,
        "Own Wind":1,
        "Honor Tile - White":1,
        "Honor Tile - Green":1,
        "Honor Tile - Red":1,
        "Straight":2,
        "Straight (open)":1,
        "3 Color Straights":2,
        "3 Color Straights (open)": 1,
        "3 Color Triplets":2,
        "3 Concealed Triplets":2,
        "3 Quads":2,
        "Mixed Terminals":2,
        "Chanta":2,
        "Chanta (open)":1,
        "Junchan":3,
        "Junchan (open)":2,
        "2Peko":3,

        "Semi-Flush":3,
        "Semi-Flush (open)":2,
        "Flush":6,
        "Flush (open)":5
    }

    han = 0
    for yaku in yakulist_:
        han += handict[yaku]

    return han


def count_limit(yakulist_):
    limitdict = {
        "4 Concealed Triplets":1,
        "4 Concealed Triplets (single wait)": 2,
        "Little 4 Winds":1,
        "Big 4 Winds":2,
        "13 Orphans":1,
        "13 Orphans (13 waits)":2,
        "Nine Gates":1,
        "Nine Gates (nine waits)":2,
        "All Honors":1,
        "All Terminals":1,
        "All Green":1,
        "Big 3 Dragons":1,
        "4 Quads":1,
        "Heavenly Hand":1,
        "Earth Hand":1
    }

    limit = 0
    for yaku in yakulist_:
        limit += limitdict[yaku]

    return limit


def calculate_score(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_, riichi_, oneshot_, last_, robbing_kong_, doras_, u_doras_):

    # 念のため並び替え
    closedhandstr_ = arrange_tile(closedhandstr_)
    # 面子の取り方ごとに再起させる
    # 特殊形式だけ先に計算する。
    # 国士と考えてチェック
    kokushi_checker = [0] * 13
    kokushi_id = ["1m", "9m", "1p", "9p", "1s", "9s", "1z", "2z", "3z", "4z", "5z", "6z", "7z"]
    double_check = False
    failure_flag = False
    try:
        if len(exposedstrlist_) == 0 and len(closedhandstr_) == 2*13:
            for i in range(13):
                needle_pai = closedhandstr_[i*2:i*2+2]
                needle_id = kokushi_id.index(needle_pai)
                kokushi_checker[needle_id] += 1
            # 合計が13, 2のものは最大で1つであること
            for i in range(13):
                if kokushi_checker[i] == 2 and not double_check:
                    double_check = True
                elif kokushi_checker[i] == 2 and double_check:
                    failure_flag = True
                elif kokushi_checker[i] > 2:
                    failure_flag = True

    except ValueError:
        #国士ではないことが確定
        failure_flag = True

    #国士待ち確定した場合
    # 単騎待ち
    if not failure_flag:
        if double_check and winningpai_ in kokushi_id and kokushi_checker[winningpai_] == 0:
            #国士無双成立
            points = getpoints("Limit", "Limit", is_dealer_, winbyself_)
            yaku_list = ["13 Orphans"]

        #13麺町かどうか
        elif not double_check and winningpai_ in kokushi_id:
            #13麺待ちダブル約万
            points = getpoints("Limit2", "Limit2", is_dealer_, winbyself_)
            yaku_list = ["13 Orphans - 13 wait"]

    # lrgal check
    # 暫定措置として、最初にヒットした待ちだけ
    machiform = machi(closedhandstr_, exposedstrlist_)
    maxscore = 0
    maxresult = None
    for waits in machiform:
        if winningpai_.replace("0", "5") in waits[1]:
            # 結果表示
            # 面前部分作成
            menzenpart = []
            for meld in waits[0]:
                if not meld.startswith("{"):
                    menzenpart.append(meld)
            result = calculate_score_one(menzenpart, exposedstrlist_, winningpai_,
                                         winbyself_, is_dealer_, prevailingwind_, ownwind_,
                                         riichi_, oneshot_, last_, robbing_kong_, doras_, u_doras_)

            nowscore = int(re.split(r"A|\-", result[0])[0])

            # この点数がmaxscoreを超えていたなら書き換える
            if nowscore > maxscore:
                maxresult = result
                maxscore = nowscore

    return maxresult

    print("Error maybe")

    # 七トイツと考えて調べる

# 一列化
def serialize(closedhandstr_, exposes_, winningpai_):
    serialhand = ""
    for meld in closedhandstr_:
        serialhand += meld.strip("()[]")
    for meld in exposes_:
        serialhand += meld.strip("{}")
    serialhand += winningpai_

    return serialhand

# 単独ハイチェック
def paicheck_simple(haicode_):
    return haicode_[1] != "z" and int(haicode_[0]) >= 2 and int(haicode_[0]) <= 8


def paicheck_green(haicode_):
    if haicode_ == "6z":
        return True
    elif int(haicode_[0]) in [2,3,4,6,8] and haicode_[1] == "s":
        return True
    else:
        return False

def paicheck_honor(haicode_):
    return haicode_[1] == "z"

def paicheck_terminal(haicode_):
    return (haicode_[0] == "1" or haicode_[0] == "9") and haicode_[1] != "z"

def paicheck_orphan(haicode_):
    return paicheck_terminal(haicode_) or paicheck_honor(haicode_)


# 完成面子 () 副露 {}
# 完成頭 []
# 待ち　なし
# (1m2m3m), (3m4m5m), [2p2p],
def meld(closedhandstr_, exposes_, winningpai_, tsumo_=True):
    hands = []
    for menzu in closedhandstr_:
        if menzu[0] == "(":
            hands.append("({0})".format(menzu.strip("()")))
        elif menzu[0] == "[":
            hands.append("[{0}]".format(menzu.strip("[]")))
        else:
            if len(menzu) == 2:
                hands.append("[{0}{1}]".format(menzu, winningpai_))
            elif len(menzu) == 4:
                # 順子の場合どっちが咲か
                sample = menzu[0:1]
                if sample < winningpai_:
                    inner = "{0}{1}".format(menzu, winningpai_)
                else:
                    inner = "{0}{1}".format(winningpai_, menzu)
                if tsumo_:
                    hands.append("({0})".format(inner))
                else:
                    hands.append("{" + inner + "}")

    hands.extend(exposes_)

    return hands


def yakucheck_yakuhai(closedhandstr_, exposes_, winningpai_, prevailingwind_, ownwind_):
    raw = debuff(meld(closedhandstr_, exposes_, winningpai_))
    yaku_list = []
    for trip in raw:
        if len(trip) > 4:
            if trip[0:2] == prevailingwind_:
                yaku_list.append("Prevailing Wind")
            if trip[0:2] == ownwind_:
                yaku_list.append("Own Wind")
            if trip[0:2] == "5z":
                yaku_list.append("Honor Tile - White")
            if trip[0:2] == "6z":
                yaku_list.append("Honor Tile - Green")
            if trip[0:2] == "7z":
                yaku_list.append("Honor Tile - Red")

    return yaku_list




# 役チェック
# たんやお
def yakucheck_simples(closedhandstr_, exposes_, winningpai_):
    serial = serialize(closedhandstr_, exposes_, winningpai_)
    serial = serial.replace("0", "5")
    for i in range(int(len(serial)/2)):
        if int(serial[i*2]) >= 2 and int(serial[i*2]) <= 8 and serial[i*2+1] != "z":
            continue
        else:
            return False
    return True


def yakucheck_1peko(closedhandstr_, exposes_, winningpai_):
    #面前チェック
    if len(exposes_) > 0:
        return False
    #おない順子があればいい。ただし2pekoは別
    melded = meld(closedhandstr_, exposes_, winningpai_)
    melded.sort()
    peko1 = ""
    sameflag = 0
    for i in range(len(melded)):
        for j in range(i+1, len(melded)):
            if melded[i] == melded[j] and melded[i][1] != melded[i][3] and melded[i] != peko1:
                sameflag += 1
                peko1 = melded[i]
    return sameflag == 1


def yakucheck_2peko(closedhandstr_, exposes_, winningpai_):
    if len(exposes_) > 0:
        return False
    #おない順子があればいい。ただし2pekoは別
    melded = meld(closedhandstr_, exposes_, winningpai_)
    melded.sort()
    peko1 = ""
    sameflag = 0
    for i in range(len(melded)):
        for j in range(i+1, len(melded)):
            if melded[i] == melded[j] and melded[i][1] != melded[i][3] and melded[i] != peko1:
                sameflag += 1
                peko1 = melded[i]
    return sameflag == 2


#3アンコウ
def yakucheck_3conceal(closedhandstr_, exposes_, winningpai_, winbydraw_):
    melded = meld(closedhandstr_, exposes_, winningpai_, winbydraw_)
    #()の刻子かカンがあるか
    concealcount = 0
    for mel in melded:
        if mel.startswith("(") and len(mel) > 6 and mel[1] == mel[3] and mel[3] == mel[5]:
            concealcount += 1

    return concealcount == 3


# 0 違う　1 普通 2 単騎待ち
def yakucheck_4conceal(closedhandstr_, exposes_, winningpai_, winbydraw_):
    melded = meld(closedhandstr_, exposes_, winningpai_, winbydraw_)
    #()の刻子かカンがあるか
    concealcount = 0
    for mel in melded:
        if mel.startswith("(") and len(mel) > 6 and mel[1] == mel[3] and mel[3] == mel[5]:
            concealcount += 1

    # conceal=4のときで、closedhandのなかに4()あれば単騎待ち
    if concealcount == 4:
        for trip in closedhandstr_:
            if len(trip) == 2:
                return 2
        return 1
    else:
        return 0

#3食同順
def yakucheck_3color_chow(closedhandstr_, exposes_, winningpai_):
    melded = debuff(meld(closedhandstr_, exposes_, winningpai_))
    melded.sort()
    #刻子と頭は除外する
    judger = []
    for elem in melded:
        if elem[0] != elem[2]:
            judger.append(elem)

    #3以上残っているか
    if len(judger) < 3:
        return False

    #各色の最初の順子を残す
    m_firsts = []
    p_firsts = []
    s_firsts = []
    for elem in judger:
        if elem[1] == "m":
            m_firsts.append(int(elem[0]))
        if elem[1] == "p":
            p_firsts.append(int(elem[0]))
        if elem[1] == "s":
            s_firsts.append(int(elem[0]))

    #m_firstsの要素がps両方にあればいい
    successflag = False
    for first in m_firsts:
        if first in p_firsts and first in s_firsts:
            successflag = True
    return successflag


#チャンタ
def yakucheck_chanta(closedhandstr_, exposes_, winningpai_):
    #全てにorphanが入っていて、１つはsimpleが入っている
    bared = debuff(meld(closedhandstr_, exposes_, winningpai_))

    simpleflag = False #1はたんやおがあるか、(ないとほんろ
    honorflag = False # 1は字牌があるか(ないとじゅんちゃん
    for ele in bared:
        yaochu_1flag = False
        for i in range(int(len(ele)/2)):
            needlepai = ele[i*2:i*2+2]
            if paicheck_orphan(needlepai):
                yaochu_1flag = True
            if paicheck_simple(needlepai):
                simpleflag = True
            if paicheck_honor(needlepai):
                honorflag = True
        #やおちゅうなしならすぐだめ
        if not yaochu_1flag:
            return False

    #全てにやおちゅーはある、字牌と中針もあればいい
    return simpleflag and honorflag


def yakucheck_junchan(closedhandstr_, exposes_, winningpai_):
    bared = debuff(meld(closedhandstr_, exposes_, winningpai_))

    simpleflag = False  # 1はたんやおがあるか、(ないとchinnro
    for ele in bared:
        yaochu_1flag = False
        for i in range(int(len(ele) / 2)):
            needlepai = ele[i * 2:i * 2 + 2]
            if paicheck_terminal(needlepai):
                yaochu_1flag = True
            if paicheck_simple(needlepai):
                simpleflag = True
        # やおちゅうなしならすぐだめ
        if not yaochu_1flag:
            return False

    # 全てにやおちゅーはある、字牌と中針もあればいい
    return simpleflag

#一気通貫
def yakucheck_straight(closedhandstr_, exposes_, winningpai_):
    melded = debuff(meld(closedhandstr_, exposes_, winningpai_))
    #1, 4, 7ではじまる順子のみ残す
    firsts = [[], [], []]
    consert = {"m":0, "p":1, "s":2}

    for trip in melded:
        if trip[0] != trip[2]:
            firsts[consert[trip[1]]].append(int(trip[0]))

    #どれかに147がそろっていれば成功
    for trophy in firsts:
        if 1 in trophy and 4 in trophy and 7 in trophy:
            return True
    #失敗なら
    return False


#対々和
def yakucheck_toitoi(closedhandstr_, exposes_, winningpai_):
    melded = meld(closedhandstr_, exposes_, winningpai_)
    #四あんこではない、全部かんかぽん
    anko4flag = True
    for trip in melded:
        if trip.startswith("{"):
            anko4flag = False
        #順子ならば終了
        if trip[1] != trip[3]:
            return  False

    #最後まで残っていれば、4ankoチェック
    return not anko4flag



#3色同刻
def yakucheck_3color_pong(closedhandstr_, exposes_, winningpai_):
    melded = debuff(meld(closedhandstr_, exposes_, winningpai_))
    melded.sort()
    #刻子と頭は除外する
    m_pons = []
    s_pons = []
    p_pons = []
    for elem in melded:
        if elem[0] == elem[2] and len(elem) > 4:
            if elem[1] == "m":
                m_pons.append(int(elem[0]))
            elif elem[1] == "s":
                s_pons.append(int(elem[0]))
            elif elem[1] == "p":
                p_pons.append(int(elem[0]))

    #m_firstsの要素がps両方にあればいい
    successflag = False
    for first in m_pons:
        if first in p_pons and first in s_pons:
            successflag = True
    return successflag


def yakucheck_3quads(closedhandstr_, exposes_, winningpai_):
    raw = debuff(meld(closedhandstr_, exposes_, winningpai_))

    quads_count = 0
    for trip in raw:
        if len(trip) == 8:
            quads_count += 1

    return quads_count == 3


def yakucheck_4quads(closedhandstr_, exposes_, winningpai_):
    raw = debuff(meld(closedhandstr_, exposes_, winningpai_))

    quads_count = 0
    for trip in raw:
        if len(trip) == 8:
            quads_count += 1

    return quads_count == 4

#ほんいつ
def yakucheck_semiflush(closedhandstr_, exposes_, winningpai_):
    #字牌1異常と崇拝一種類
    serial = serialize(closedhandstr_, exposes_, winningpai_)
    honorcontain_check = "z" in serial
    if honorcontain_check:
        #1種類のみなら成功
        flagnumber = 0
        if "m" in serial:
            flagnumber += 1
        if "p" in serial:
            flagnumber += 2
        if "s" in serial:
            flagnumber += 4
        if flagnumber in [1,2,4]:
            return True
    return False


#ちんいつ
def yakucheck_flush(closedhandstr_, exposes_, winningpai_):
    #字牌1異常と崇拝一種類
    serial = serialize(closedhandstr_, exposes_, winningpai_)
    honorcontain_check = "z" in serial
    if not honorcontain_check:
        # 1種類のみなら成功
        flagnumber = 0
        if "m" in serial:
            flagnumber += 1
        if "p" in serial:
            flagnumber += 2
        if "s" in serial:
            flagnumber += 4
        if flagnumber in [1, 2, 4]:
            return True
    return False


def yakucheck_allgreen(closedhandstr_, exposes_, winningpai_):
    serial = serialize(closedhandstr_, exposes_, winningpai_)
    for i in range(int(len(serial)/2)):
        if not paicheck_green(serial[i*2:i*2+2]):
            return False
    return True

#字一色
def yakucheck_allhonor(closedhandstr_, exposes_, winningpai_):
    #全て字牌
    serial = serialize(closedhandstr_, exposes_, winningpai_)
    for i in range(int(len(serial)/2)):
        if not paicheck_honor(serial[i*2:i*2+2]):
            return False
    return True


#珍郎党
def yakucheck_allterminal(closedhandstr_, exposes_, winningpai_):
    #全て19 terminal
    serial = serialize(closedhandstr_, exposes_, winningpai_)
    for i in range(int(len(serial)/2)):
        if not paicheck_terminal(serial[i*2:i*2+2]):
            return False
    return True

#大三元
def yakucheck_big3dragon(closedhandstr_, exposes_, winningpai_):
    melded = meld(closedhandstr_, exposes_, winningpai_)
    raw = debuff(melded)
    flagnumber = 0
    for elem in raw:
        if elem.startswith("5z5z5z"):
            flagnumber += 1
        elif elem.startswith("6z6z6z"):
            flagnumber += 10
        elif elem.startswith("7z7z7z"):
            flagnumber += 100

    return flagnumber == 111

#小三元
def yakucheck_little3dragon(closedhandstr_, exposes_, winningpai_):
    melded = meld(closedhandstr_, exposes_, winningpai_)
    raw = debuff(melded)
    flagnumber = 0
    for elem in raw:
        if elem.startswith("5z5z5z"):
            flagnumber += 1
        elif elem.startswith("6z6z6z"):
            flagnumber += 10
        elif elem.startswith("7z7z7z"):
            flagnumber += 100
        # 頭の場合
        if elem == "5z5z":
            flagnumber += 3
        elif elem == "6z6z":
            flagnumber += 30
        elif elem == "7z7z":
            flagnumber += 300

    return flagnumber in [113, 131, 311]


#大四喜
def yakucheck_big4wind(closedhandstr_, exposes_, winningpai_):
    melded = meld(closedhandstr_, exposes_, winningpai_)
    raw = debuff(melded)
    flagnumber = 0
    headnumber = 0
    for elem in raw:
        if elem.startswith("1z1z1z"):
            flagnumber += 1
        elif elem.startswith("2z2z2z"):
            flagnumber += 10
        elif elem.startswith("3z3z3z"):
            flagnumber += 100
        elif elem.startswith("4z4z4z"):
            flagnumber += 1000

    return flagnumber == 1111

#小四喜
def yakucheck_little4wind(closedhandstr_, exposes_, winningpai_):
    melded = meld(closedhandstr_, exposes_, winningpai_)
    raw = debuff(melded)
    flagnumber = 0
    headnumber = 0
    for elem in raw:
        if elem.startswith("1z1z1z"):
            flagnumber += 1
        elif elem.startswith("2z2z2z"):
            flagnumber += 10
        elif elem.startswith("3z3z3z"):
            flagnumber += 100
        elif elem.startswith("4z4z4z"):
            flagnumber += 1000

    # あたまぶぶん
    for elem in raw:
        if elem == "1z1z":
            flagnumber += 3
        elif elem == "2z2z":
            flagnumber += 30
        elif elem == "3z3z":
            flagnumber += 300
        elif elem == "4z4z":
            flagnumber += 3000

    return flagnumber in [1113, 1131, 1311, 3111]


#厨連邦党　数字で返す 2なら純正
def yakucheck_ninegates(closedhandstr_, exposes_, winningpai_):
    # 一色かつ全部で1-3 9-3
    if len(exposes_) > 0:
        return 0

    if not yakucheck_flush(closedhandstr_, exposes_, winningpai_):
        return 0

    gates = [0] * 9
    serial = serialize(closedhandstr_, exposes_, winningpai_)
    for i in range(int(len(serial)/2)):
        gates[int(serial[i*2])-1] += 1

    #特定のやつをひくと、1つだけ1になっていればいい
    gates[0] -= 3
    gates[8] -= 3
    for i in range(1, 8):
        gates[i] -= 1
    zeros = 0
    ones = 0
    one_index = -1
    for i in range(9):
        if gates[i] == 0:
            zeros += 1
        elif gates[i] == 1:
            ones += 1
            one_index = i

    if zeros == 8 and ones == 1:
        if int(winningpai_[0]) == one_index + 1:
            return 2
        else:
            return 1
    else:
        return 0



def debuff(melds_):
    newmeld = []
    for elem in melds_:
        newmeld.append(elem.strip("{}()[]"))
    return newmeld


def getpoints(fu_, han_, is_dealer_, winbyself_):

    comment = ""
    fuhan = ""

    if str(fu_).startswith("Limit"):
        # 何倍役満か
        if len(fu_) > 5:
            times = int(fu_[5])
        else:
            times = 1

        purescore = SCORE_CHILD_MANGAN * 4 * times
        comment = str(times) + "Limits"

    else:
        if fu_ == 25:
            purescore = fu_
        elif fu_ % 10 == 0:
            purescore = fu_
        else:
            purescore = fu_ + 10 - (fu_ % 10)
        fuhan = "{}fu{}han".format(purescore, han_)

        #場ぞろ
        purescore *= 4

        #潘
        if han_ < 6:
            purescore = purescore * (2 ** han_)

        # 2000異常なら満貫扱い
        if purescore >= 2000 or han_ >= 5:
            # 満貫扱い
            if han_ < 6:
                purescore = 2000
                comment = "Mangan"
            elif han_ < 8:
                purescore = 3000
                comment = "Haneman"
            elif han_ < 11:
                purescore = 4000
                comment = "2Mangan"
            elif han_ < 13:
                purescore = 6000
                comment = "3Mangan"
            else:
                purescore = 8000
                comment = "Kazoe-Yakuman"
            points = purescore
    #そうでないならふけいさん
    if is_dealer_:
        if winbyself_:
            points = str(kiriage100(purescore*2)) + "All"
        else:
            points = str(kiriage100(purescore*6))
    else:
        if winbyself_:
            points = "{0}-{1}".format(kiriage100(purescore), kiriage100(purescore*2))
        else:
            points = str(kiriage100(purescore*4))

    return points, comment


def kiriage100(purepoint_):
    if purepoint_ % 100 == 0:
        return  purepoint_
    else:
        return purepoint_ + 100 - (purepoint_ % 100)


def shanten(tileliststr_, exposes_=[]):
    kokushi_shanten = shanten_kokushi(tileliststr_)
    sevenpairs_shanten = shanten_sevenpairs(tileliststr_)
    normal_shanten = shanten_normal(tileliststr_, exposes_)

    return normal_shanten, sevenpairs_shanten, kokushi_shanten

def shanten_kokushi(tileliststr_):
    start_shanten = 13
    toitsu_flag = False
    kokushi_parts = ["1m", "9m", "1p", "9p", "1s", "9s", "1z", "2z", "3z", "4z", "5z", "6z", "7z"]
    for kokushi_part in kokushi_parts:
        if kokushi_part in tileliststr_:
            start_shanten -= 1
        # 1つまで重複を許す
        if (kokushi_part + kokushi_part) in tileliststr_ and not toitsu_flag:
            start_shanten -= 1
            toitsu_flag = True

    return  start_shanten

def shanten_sevenpairs(tileliststr_):
    # 長さが足りない場合はそもそもなし
    if len(tileliststr_) < 2 * 13:
        return 6


    pairs = 0
    # 0 を 5 に書き換える
    tileliststr_ = tileliststr_.replace('0', '5')
    # 仮実装　トイツだけみる
    needle = 0
    while needle <= 12:
        if tileliststr_[needle*2:needle*2+2] == tileliststr_[needle*2+2:needle*2+4]:
            pairs += 1
            needle += 2
        else:
            needle += 1

    return 6 - pairs

def shanten_normal(handstr_, exposed_=[]):
    # m p sで区切る
    manzu = ""
    pinzu = ""
    souzu = ""
    honors = ""
    for i in range(int(len(handstr_) / 2)):
        if handstr_[2*i+1] == "m":
            manzu += handstr_[2*i]
        elif handstr_[2*i+1] == "s":
            souzu += handstr_[2*i]
        elif handstr_[2*i+1] == "p":
            pinzu += handstr_[2*i]
        elif handstr_[2*i+1] == "z":
            honors += handstr_[2*i]

    # 数字返還
    manzu = encode_tilescape(manzu)
    pinzu = encode_tilescape(pinzu)
    souzu = encode_tilescape(souzu)
    honors = encode_tilescape(honors)

    # 頭なしの場合
    headless_score = optimize_melds(manzu, pinzu, souzu, honors, 4 - len(exposed_))
    max_score = headless_score

    # 頭を順に仮定する。この場合はscoreに+1して比較する
    numbers = [manzu, pinzu, souzu, honors]
    for i in range(4):
        for id in range(len(numbers[i])):
            if int(numbers[i][id]) >= 2:
                numbers[i] = numbers[i][0:id] + str(int(numbers[i][id]) - 2) + numbers[i][id+1:]
                # この状態で解析
                tempscore = optimize_melds(numbers[0], numbers[1], numbers[2], numbers[3], 4 - len(exposed_)) + 1
                max_score =max(max_score, tempscore)
                # 元に戻す
                numbers[i] = numbers[i][0:id] + str(int(numbers[i][id]) + 2) + numbers[i][id+1:]

    return 8 - max_score - len(exposed_) * 2


def encode_tilescape(tileliststr_):
    encode = ""
    for i in range(1, 10):
        encode += str(tileliststr_.count(str(i)))

    return encode


def disintegrate_code(colorcode_):
    # 孤立杯を分解する
    colorcode_.strip('0')
    blocks = colorcode_.split('00')

    #各ブロックについてさらに
    for i in range(len(blocks)):
        blocks[i] = blocks[i].strip('0')

    # 1と空文字は除外
    blocks = [s for s in blocks if s != "1" and len(s) > 0]

    return blocks


def optimize_melds(m_code, p_code, s_code, h_code, max_mentsu=4):
    # それぞれでblocksを作って合体させる
    blocks = []
    blocks.extend(disintegrate_code(m_code))
    blocks.extend(disintegrate_code(p_code))
    blocks.extend(disintegrate_code(s_code))

    meld_candidate = [[0 for i in range(4)] for j in range(len(blocks)+1)]
    for i in range(len(blocks)):
        # 孤立杯除去
        try:
            alpha_number = meldstable[blocks[i]].zfill(4)
        except KeyError as e:
            alpha_number = 1010
        for j in range(4):
            meld_candidate[i][j] = int(alpha_number[j])

    #字牌は2が面子候補、3,4が面子
    count2 = h_code.count('2')
    count3more = h_code.count('3') + h_code.count('4')
    meld_candidate[len(blocks)][0] = count3more
    meld_candidate[len(blocks)][1] = count2
    meld_candidate[len(blocks)][2] = count3more
    meld_candidate[len(blocks)][3] = count2

    #8通りの取り方を順に試す
    for pattern in range(2**len(blocks)):
        completed_meld = 0
        candidate = 0
        # manzu
        for tester in range(len(blocks)):
            if pattern & 2**tester == 2**tester:
                completed_meld += meld_candidate[tester][0]
                candidate += meld_candidate[tester][1]
            else:
                completed_meld += meld_candidate[tester][2]
                candidate += meld_candidate[tester][3]
        #字牌
        completed_meld += meld_candidate[len(blocks)][0]
        candidate += meld_candidate[len(blocks)][1]

        if completed_meld > max_mentsu:
            completed_meld = max_mentsu
            candidate = 0
        if (completed_meld + candidate) > max_mentsu:
            candidate = max_mentsu - completed_meld

        return completed_meld * 2 + candidate


def arrange_tile(handstr_):
    def tile_index(tilecode):
        index = 0
        index += int(tilecode[0])
        # 赤なら5扱い
        if tilecode[0] == "0":
            index += 4.5

        if tilecode[1] == "p":
            index += 10
        elif tilecode[1] == "s":
            index += 20
        elif tilecode[1] == "z":
            index += 30

        return index

    # 2ごとに分ける
    handlist = []
    for i in range(int(len(handstr_) / 2)):
        handlist.append(handstr_[i*2:i*2+2])

    handlist.sort(key=tile_index)
    return "".join(handlist)


def machi(handstr_, exposes_):
    # 手の長さチェック
    closed_len = int(len(handstr_) / 2)
    if closed_len + len(exposes_) * 3 != 13:
        raise Exception("handstr_:{}, ex{}".format(handstr_, exposes_))

    # 赤はいの保存
    redm_flag = False
    redp_flag = False
    reds_flag = False
    if "0m" in handstr_:
        redm_flag = True
    if "0p" in handstr_:
        redp_flag = True
    if "0s" in handstr_:
        reds_flag = True

    # handstrの理牌
    handstr_ = arrange_tile(handstr_.replace('0', '5'))
    # 要求される面子数　exposeの数だけ減る
    required_melds = 4 - len(exposes_)

    # 3面子１頭と４面子頭待ちとに分ける
    serial = "".join(handstr_)


    # 国士夢想と考えるパターン
    # 全てがか
    handlist = disintegrate_hand(handstr_)

    def kokuchi_eater(handlist_):
        if len(handlist_) != 13:
            return []
        onelist = ["1m", "9m", "1s", "9s", "1p", "9p", "1z", "2z", "3z", "4z", "5z", "6z", "7z"]
        twolist = []
        for hai in handlist_:
            if not paicheck_orphan(hai):
                return []
            if hai in onelist:
                onelist.remove(hai)
                continue
            elif len(twolist) > 0:
                return []
            else:
                twolist.append(hai)

        #全部終了時、onelistが空っぽなら、まるまる
        if len(onelist) == 0:
            return [["1m9m1s9s1p9p1z2z3z4z5z6z7z"],
            ["1m", "9m", "1s", "9s", "1p", "9p", "1z", "2z", "3z", "4z", "5z", "6z", "7z"]]
        else:
            return [handstr_, twolist]

    # 4面子頭待ちとして考える

    def mentsu_eater(rest_):

        # 頭１つに確定したらそれを返す
        if len(rest_) == 2:
            return [[rest_]]

        # 頭の古紙で考える

        thislevel = []
        nextrestlist = []

        # 基準はいは全て
        found_flag = False
        for pai in TILE_TABLE:

            # 順子チェック
            if not paicheck_honor(pai) and int(pai[0]) < 8:
                nextpai = paicode_next(pai)
                nextnext = paicode_next(nextpai)
                # 全てある場合は取り出す
                if pai in rest_ and nextpai in rest_ and nextnext in rest_:
                    # 取り出した結果　余りが1つだけなら成功
                    nextrestlist.append(remove_from_hand(rest_, [pai, nextpai, nextnext]))
                    thislevel.append("({0}{1}{2})".format(pai, nextpai, nextnext))
                    found_flag = True

            # 刻子チェック
            pong = pai + pai + pai
            if pong in rest_:
                pongstart = rest_.index(pong)
                newrest = rest_[0:pongstart] + rest_[pongstart+6:]
                nextrestlist.append(newrest)
                thislevel.append("({0})".format(pong))
                found_flag = True

            # 同じグループ内で発見済みなら終了
            if found_flag and pai[0] == "9":
                break



        answer_list = []

        for i in range(len(nextrestlist)):
            inner = mentsu_eater(nextrestlist[i])

            for inn in inner:
                inn.append(thislevel[i])
                answer_list.append(inn)

        return answer_list

    # 面子候補待ちと考える方式
    def head_eater(rest_):
        # 頭待ちではないので、頭を一つ仮定して回していく
        head_candidate_list = []
        restlist = []
        for eye in TILE_TABLE:
            if (eye + eye) in rest_:
                head_candidate_list.append("[{0}{1}]".format(eye, eye))
                eyeid = rest_.index(eye)
                newrest = rest_[0:eyeid] + rest_[eyeid+4:]
                restlist.append(newrest)

        def mentsu_waitor(rest_):
            #残り2で、同じか連続なら返す
            if len(rest_) <= 4:
                if rest_[0:2] == rest_[2:4]:
                    return [[rest_]]
                elif rest_[1] != "z" and rest_[3] != "z" and rest_[1] == rest_[3] and paicode_next(rest_[0:2]) == rest_[2:4]:
                    return [[rest_]]
                elif rest_[1] != "z" and rest_[3] != "z" and rest_[1] == rest_[3] and paicode_next(paicode_next(rest_[0:2])) == rest_[2:4]:
                    return [[rest_]]
                
            thislevel = []
            nextrestlist = []

            found_flag = False
            for pai in TILE_TABLE:

                # 順子チェック
                if not paicheck_honor(pai) and int(pai[0]) < 8:
                    nextpai = paicode_next(pai)
                    nextnext = paicode_next(nextpai)
                    # 全てある場合は取り出す
                    if pai in rest_ and nextpai in rest_ and nextnext in rest_:
                        # 取り出した結果　余りが1つだけなら成功
                        nextrestlist.append(remove_from_hand(rest_, [pai, nextpai, nextnext]))
                        thislevel.append("({0}{1}{2})".format(pai, nextpai, nextnext))
                        found_flag = True

                # 刻子チェック
                pong = pai + pai + pai
                if pong in rest_:
                    pongstart = rest_.index(pong)
                    newrest = rest_[0:pongstart] + rest_[pongstart+6:]
                    nextrestlist.append(newrest)
                    thislevel.append("({0})".format(pong))
                    found_flag = True

                # 同じグループ内で発見済みなら終了
                if found_flag and pai[0] == "9":
                    break

            answer_list = []

            for i in range(len(nextrestlist)):
                inner = mentsu_waitor(nextrestlist[i])

                for inn in inner:
                    inn.append(thislevel[i])
                    answer_list.append(inn)

            return answer_list

        answer_list = []
        for i in range(len(head_candidate_list)):
            waitor = mentsu_waitor(restlist[i])
            for waiting in waitor:
                waiting.append(head_candidate_list[i])
                answer_list.append(waiting)

        return answer_list

    def pair_eater(serial):
        answer_list = []

        if shanten_sevenpairs(serial) == 0:
            waits = []
            needle = 0
                # 隣と同じかどうかを調べる
            while needle <= 12:
                if needle <= 11 and serial[needle*2:needle*2+2] == serial[needle*2+2:needle*2+4]:
                    waits.append("[{0}]".format(serial[needle*2:needle*2+4]))
                    needle += 2
                else:
                    waits.append(serial[needle*2:needle*2+2])
                    needle += 1

            answer_list.append(waits)

        else:
            pass

        return answer_list

    waiting_mentsu = head_eater(serial)
    sampler = mentsu_eater(serial)
    pairs = pair_eater(serial)
    kokushiable = kokuchi_eater(serial)

    sampler.extend(waiting_mentsu)
    sampler.extend(pairs)
    sampler.extend(kokushiable)

    # それぞれsortして、完全一致しているものがあれば削除する
    for sample in sampler:
        sample.sort()

    deleteist = []
    for i in range(len(sampler)):
        for j in range(i + 1, len(sampler)):
            sameflag = True
            for k in range(len(sampler[i])):
                if sampler[i][k] != sampler[j][k]:
                    sameflag = False
                    break
            if sameflag:
                deleteist.append(j)

    newsampler = []

    for i in range(len(sampler)):
        if not i in deleteist:
            newsampler.append(sampler[i])

    #副露部分の追加
    for i in range(len(newsampler)):
        newsampler[i].extend(exposes_)

    # 具体的な待ち牌を付け加える
    result = []
    try:
        for i in range(len(newsampler)):
            for j in range(len(newsampler[i])):
                if not newsampler[i][j][0] in "{[(":
                    if len(newsampler[i][j]) == 2:
                        waits = [newsampler[i][j]]
                    elif newsampler[i][j][0:2] == newsampler[i][j][2:4]:
                        waits = [newsampler[i][j][0:2]]
                    #数は胃連続
                    elif paicode_next(newsampler[i][j][0:2]) == newsampler[i][j][2:4]:
                        waits = []
                        #両面
                        if paicheck_simple(newsampler[i][j][0:2]):
                            waits.append(paicode_prev(newsampler[i][j][0:2]))
                        if paicheck_simple(newsampler[i][j][2:4]):
                            waits.append(paicode_next(newsampler[i][j][2:4]))
                    elif paicode_next(paicode_next(newsampler[i][j][0:2])) == newsampler[i][j][2:4]:
                        waits = [paicode_next(newsampler[i][j][0:2])]

            result.append((newsampler[i], waits))
    except:
        print()
    # 最初から見ていって、最初に出てきた黒はいを赤に返る
    newres = []
    redm_cache = redm_flag
    reds_cache = reds_flag
    redp_cache = redp_flag

    for machiform in result:
        redm_flag = redm_cache
        reds_flag = reds_cache
        redp_flag = redp_cache

        newtehai = []
        for tehai in machiform[0]:
            newstr = tehai
            if "5m" in tehai and redm_flag:
                redm_flag = False
                needle = tehai.find("5m")
                newstr = needle_replace(newstr, needle, "0")
            elif "5s" in tehai and reds_flag:  # m,s,pがいメンツの中には登場しないからelseでよい
                reds_flag = False
                needle = tehai.find("5s")
                newstr = needle_replace(newstr, needle, "0")
            elif "5p" in tehai and redp_flag:
                redp_flag = False
                needle = tehai.find("5p")
                newstr = needle_replace(newstr, needle, "0")
            newtehai.append(newstr)
        newmachi = [newtehai, machiform[1]]
        newres.append(newmachi)

    return newres


def needle_replace(rawstr_, needle_, replaced_):
    liststr = list(rawstr_)
    liststr[needle_] = replaced_
    return "".join(liststr)

def tileid_from_str(tileidstr_):
    index = 0
    index += int(tileidstr_[0])
    # 赤なら5扱い
    if tileidstr_[0] == "0":
        index += 4.5

    if tileidstr_[1] == "p":
        index += 10
    elif tileidstr_[1] == "s":
        index += 20
    elif tileidstr_[1] == "z":
        index += 30

    return index


def check_call(handstr_, discarded_):
    #listに変換
    discarded_ = discarded_.replace("0", "5")
    handstr_black = arrange_tile(handstr_.replace("0", "5"))
    handlist = []
    for i in range(int(len(handstr_black)/2)):
        handlist.append(handstr_black[i*2:i*2+2])
    handlist.sort(key=tileid_from_str)

    result = {
        "Pon":[],
        "Kan":[],
        "Chii":[]
    }

    #チーは、前2があればいい
    if not paicheck_honor(discarded_):
        #かんちゃんけい
        if int(discarded_[0]) >= 2 and int(discarded_[0]) <= 8:
            if paicode_prev(discarded_) in handlist and paicode_next(discarded_) in handlist:
                result["Chii"].append([paicode_prev(discarded_), paicode_next(discarded_)])
        if int(discarded_[0]) >= 3:
            if paicode_prev(discarded_) in handlist and paicode_prev(paicode_prev(discarded_)) in handlist:
                result["Chii"].append([paicode_prev(discarded_), paicode_prev(paicode_prev(discarded_))])
        if int(discarded_[0]) <= 7:
            if paicode_next(discarded_) in handlist and paicode_next(paicode_next(discarded_)) in handlist:
                result["Chii"].append([paicode_next(discarded_), paicode_next(paicode_next(discarded_))])

    #ポンのチェック
    if handlist.count(discarded_) >= 2:
        # 赤対応
        if paicheck_redpossible(discarded_):
            # 赤を持っていたら、持っているパターンも登録する
            if discarded_.replace("5", "0") in handstr_:
                result["Pon"].append([discarded_, discarded_.replace("5", "0")])
            # 2枚持っているなら
            if handlist.count(discarded_) >= 3 or discarded_.replace("5", "0") not in handstr_:
                result["Pon"].append([discarded_, discarded_])
        else:
            result["Pon"].append([discarded_, discarded_])

    if handlist.count(discarded_) >= 3:
        result["Kan"].append([discarded_, discarded_, discarded_])

    return result


def paicheck_redpossible(paicode_):
    if paicode_[1] != "z":
        if paicode_[0] == "5" or paicode_[0] == "0":
            return True
    else:
        return False


def remove_from_hand(handstr_, removelist_):
    ids = [-2]
    for rm in removelist_:
        ids.append(handstr_.index(rm))

    result = ""
    for i in range(len(ids) - 1):
        result += handstr_[ids[i]+2:ids[i+1]]
    result += handstr_[ids[len(ids)-1]+2:]

    return result


TILE_TABLE = ["1m","2m","3m","4m","5m", "6m","7m","8m","9m",
                    "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
                    "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
                    "1z", "2z", "3z", "4z", "5z", "6z", "7z"]

DORA_TABLE = ["2m","3m","4m","5m", "6m","7m","8m","9m", "1m",
                    "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p", "1p",
                    "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s", "1s",
                    "2z", "3z", "4z", "1z", "6z", "7z", "5z"]


def dora_from_indicator(doraindicator_):
    doraindicator_ = doraindicator_.replace("0", "5")
    tileid = TILE_TABLE.index(doraindicator_)
    return DORA_TABLE[tileid]


def paicode_next(paicode_):
    return TILE_TABLE[TILE_TABLE.index(paicode_) + 1]

def paicode_prev(paicode_):
    return TILE_TABLE[TILE_TABLE.index(paicode_) - 1]


def disintegrate_hand(handstr_):
    handlist = []
    for i in range(int(len(handstr_) / 2)):
        handlist.append(handstr_[i*2:i*2+2])
    return handlist

def logic_tile2(handstr_, known_tiles={}):
    # 並び替え
    handlist = tile_disintegrate(handstr_.replace("0", "5"))

    # シャンテン数が向上する巣手配
    upgraders = {}

    # 名に切る問題だが、まずは現在のシャンテン数を出す
    nowshanten = shanten(handstr_)[0]

    # キル杯ごとに、何を積もればシャンテン数が上がるのかを計算する
    for i in range(len(handlist)):
        # 2回目以降の出現なら次へ
        if handlist.index(handlist[i]) != i:
            continue

        upgraders[handlist[i]] = 0

        for tsumo in TILE_TABLE:
            # 新しい手配リストを作って、そのシャンテン数と有効杯の枚数を求める
            if handlist.count(tsumo) >= 4:
                continue

            temphand = [tsumo]
            for j in range(len(handlist)):
                if i != j:
                    temphand.append(handlist[j])
            # この状態でシャンテン数を出す
            temphand.sort(key=tile_index)
            nextshanten = shanten("".join(temphand))[0]
            # シャンテン数が減っているなら、記録する
            if nextshanten < nowshanten:
                upgraders[handlist[i]] += 4
                # 既に使用済みがあるならその分減らす
                if tsumo in known_tiles:
                    upgraders[handlist[i]] -= known_tiles.count(tsumo)
                upgraders[handlist[i]] -= handlist.count(tsumo)

    # 役牌だけ+1する
    yakuhai = ["5z", "6z", "7z"]
    for yakuh in yakuhai:
        if yakuh in upgraders:
            upgraders[yakuh] -= 1

    return upgraders


def logic_tile(handstr_, exposes_=[], known_tiles={}):
    # 並び替え
    handlist = tile_disintegrate(handstr_.replace("0", "5"))

    # シャンテン数が向上する巣手配
    upgraders = {}

    # 名に切る問題だが、まずは現在のシャンテン数を出す
    nowshanten = shanten(handstr_, exposes_)[0]

    # キル杯ごとに、何を積もればシャンテン数が上がるのかを計算する
    for i in range(len(handlist)):
        # 2回目以降の出現なら次へ
        if handlist.index(handlist[i]) != i:
            continue

        upgraders[handlist[i]] = 0

        for tsumo in TILE_TABLE:
            # 新しい手配リストを作って、そのシャンテン数と有効杯の枚数を求める
            if handlist.count(tsumo) >= 4:
                continue

            temphand = [tsumo]
            for j in range(len(handlist)):
                if i != j:
                    temphand.append(handlist[j])
            # この状態でシャンテン数を出す
            temphand.sort(key=tile_index)
            nextshanten = shanten("".join(temphand), exposes_)[0]
            # シャンテン数が減っているなら、記録する
            if nextshanten < nowshanten:
                upgraders[handlist[i]] += 4
                # 既に使用済みがあるならその分減らす
                try:
                    if tsumo in known_tiles:
                        upgraders[handlist[i]] -= known_tiles.count(tsumo)
                    upgraders[handlist[i]] -= handlist.count(tsumo)
                except TypeError as e:
                    input()
                    print(e.__str__())

    return upgraders


# 和了可能かどうかを調べる
def winnable_check(score_):
    yakulist = score_[2]
    for yaku in yakulist:
        if "Dora" not in yaku:
            return True
    return False


def tile_index(tilecode):
    index = 0
    try:
        index += int(tilecode[0])
    except:
        print()
    # 赤なら5扱い
    if tilecode[0] == "0":
        index += 4.5

    if tilecode[1] == "p":
        index += 10
    elif tilecode[1] == "s":
        index += 20
    elif tilecode[1] == "z":
        index += 30

    return index


def tile_disintegrate(handstr_):
    handlist = []
    for i in range(int(len(handstr_)/2)):
        handlist.append(handstr_[i*2:i*2+2])
    handlist.sort(key=tile_index)

    return handlist


def safety_zone(pond_, all_=[]):
    safety = []
    # 現物
    safety.append([])
    for tile in pond_:
        if tile not in safety[0]:
            safety[0].append(tile)

    # ほぼ安全なもの
    # 1枚以上切れた字牌、スジあり1-9、
    safety.append([])
    for tile in safety[0]:
        if tile[1] != "z":
            linelist = []
            if int(tile[0]) > 3 and int(tile[0]) < 7:
                lowline = str(int(tile[0])-3) + tile[1]
                linelist.append(lowline)
                highline = str(int(tile[0])+3) + tile[1]
                linelist.append(highline)
            for line in linelist:
                if not line in safety[0] and not line in safety[1]:
                    safety[1].append(line)

    if "2m" in safety[0] and "8m" in safety[0]:
        safety[1].append("5m")
    if "2p" in safety[0] and "8p" in safety[0]:
        safety[1].append("5p")
    if "2s" in safety[0] and "8s" in safety[0]:
        safety[1].append("5s")

    return safety


if __name__ == '__main__':

    problemfile = open("p_normal_10000.txt")

    hand = ["(1p2p3p)", "(4p0p6p)", "1p1p", "(7p8p9p)", "[9p9p]"]
    naki = ["{1p1p1p}"]
    agari = "7p"

    hand = '6m7m8m2p2p0p6p7p8p9p7s8s9s'
    naki = []


    result = calculate_score(hand, naki, agari, True, False, "2z", "2z", 1, False, False, False, ["5m"], [])


    for line in problemfile:
        parts = line.split(" ")
        hand = ""
        for i in range(14):
            hand += TILE_TABLE[int(parts[i])]

        score = shanten(hand)