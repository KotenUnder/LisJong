
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


meldstable = {}
meldsfile = open("MeldsTable.txt", "r")
meldsfile.readline()
for line in meldsfile:
    parts = line.split("\t")
    meldstable[parts[0]] = int(parts[1].strip())


def calculate_fu(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_):
    fu = 20
    #面前論で10
    if len(exposedstrlist_) == 0 and not winbyself_:
        fu += 10

    #上がり方につく符
    for elem in closedhandstr_:
        if elem[0] != "(" and elem[0] != "[":
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


def calculate_score_one(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_, riichi_, oneshot_, last_, robbing_kong_, doras_):

    #
    yaku_list = []

    # ふけいさん
    fu = calculate_fu(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_)

    # 立直していたら追加
    if riichi_ == 1:
        yaku_list.append("Ready")
    elif riichi_ == 2:
        yaku_list.append("Ready 2")

    # 一発の追加
    if oneshot_:
        yaku_list.append("One Shot")

    #

    # 海底　ホー艇
    if last_:
        if winbyself_:
            yaku_list.append("Last Pick")
        else:
            yaku_list.append("Last Discard")

    # 平和の判定 tsumo20 or ron30
    if len(exposedstrlist_) == 0 and ((winbyself_ and fu == 20) or (not winbyself_ and fu == 30)):
        yaku_list.append("Peace")

    # タンヤオの判定
    if yakucheck_simples(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("All Simples")

    # 3色の判定
    if yakucheck_3color_chow(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("3 Color Straights")
    if yakucheck_3color_pong(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("3 Color Triplets")

    # 1peko, 2peko
    if yakucheck_1peko(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("1Peko")
    elif yakucheck_2peko(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("2Peko")

    # 役牌


    # ちゃん田、うんちゃん
    if yakucheck_junchan(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Junchan")
    elif yakucheck_chanta(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Chanta")

    #ほんいつけい
    if yakucheck_semiflush(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Semi-Flush")
    elif yakucheck_flush(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Flush")

    # 一気通貫
    if yakucheck_straight(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("Straight")

    # といとい
    if yakucheck_toitoi(closedhandstr_, exposedstrlist_, winningpai_):
        yaku_list.append("All Triplets")

    han = 1

    point, comment = getpoints(fu, han, is_dealer_, winbyself_)

    return point, comment, yaku_list


def count_han(yakulist_):
    handict = {
        "Ready":1,
        "Ready 2":2,
        "One Shot":1,
        "Last Pick":1,
        "Last Discard":1,
        "1Peko":1,
        "All Simples":1,
        "2Peko":3,
    }

def calculate_score(closedhandstr_, exposedstrlist_, winningpai_, winbyself_, is_dealer_, prevailingwind_, ownwind_):
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

    pass


    # lrgal check


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
def yakkucheck_big3dragon(closedhandstr_, exposes_, winningpai_):
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





def debuff(melds_):
    newmeld = []
    for elem in melds_:
        newmeld.append(elem.strip("{}()[]"))
    return newmeld


def getpoints(fu_, han_, is_dealer_, winbyself_):

    comment = ""

    if str(fu_).startswith("Limit"):
        # 何倍役満か
        if len(fu_) > 5:
            times = int(fu_[5])
        else:
            times = 1

        purescore = SCORE_CHILD_MANGAN * 4 * times
        comment = "Limit" + str(times)

    else:
        if fu_ == 25:
            purescore = fu_
        elif fu_ % 10 == 0:
            purescore = fu_
        else:
            purescore = fu_ + 10 - (fu_ % 10)
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


def shanten(tileliststr_):
    kokushi_shanten = shanten_kokushi(tileliststr_)
    sevenpairs_shanten = shanten_sevenpairs(tileliststr_)
    normal_shanten = shanten_normal(tileliststr_)

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

def shanten_normal(handstr_):
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
    headless_score = optimize_melds(manzu, pinzu, souzu, honors)

    max_score = headless_score
    # 頭を順に仮定する。この場合はscoreに+1して比較する
    numbers = [manzu, pinzu, souzu, honors]
    for i in range(4):
        for id in range(len(numbers[i])):
            if int(numbers[i][id]) >= 2:
                numbers[i] = numbers[i][0:id] + str(int(numbers[i][id]) - 2) + numbers[i][id+1:]
                # この状態で解析
                tempscore = optimize_melds(numbers[0], numbers[1], numbers[2], numbers[3]) + 1
                max_score =max(max_score, tempscore)
                # 元に戻す
                numbers[i] = numbers[i][0:id] + str(int(numbers[i][id]) + 2) + numbers[i][id+1:]

    return 8 - max_score


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

def optimize_melds(m_code, p_code, s_code, h_code):
    # それぞれでblocksを作って合体させる
    blocks = []
    blocks.extend(disintegrate_code(m_code))
    blocks.extend(disintegrate_code(p_code))
    blocks.extend(disintegrate_code(s_code))

    meld_candidate = [[0 for i in range(4)] for j in range(len(blocks)+1)]
    for i in range(len(blocks)):
        # 孤立杯除去
        alpha_number = meldstable[blocks[i]].zfill(4)
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

        if completed_meld > 4:
            completed_meld = 4
            candidate = 0
        if (completed_meld + candidate) > 4:
            candidate = 4 - completed_meld

        return completed_meld * 2 + candidate


def arrange_tile(handstr_):
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

    # 2ごとに分ける
    handlist = []
    for i in range(int(len(handstr_) / 2)):
        handlist.append(handstr_[i*2:i*2+2])

    handlist.sort(key=tile_index)
    return "".join(handlist)


def machi(handstr_, exposes_):
    # handstrの理牌
    handstr_ = arrange_tile(handstr_.replace('0', '5'))
    # 要求される面子数　exposeの数だけ減る
    required_melds = 4 - len(exposes_)

    # mpszに分ける
    colorlist = ["", "", "", ""]
    identifier = {"m":0, "p":1, "s":2, "z":3}

    for i in range(int(len(handstr_) / 2)):
        colorlist[identifier[handstr_[i*2+1]]] += handstr_[i*2:i*2+2]

    # 面子候補などの数をいれる
    candidator_combination = []
    for i in range(4):
        #candidator_combination.append(
         #   TABLE_CANDIDATOR_COMBINATION[int(len(colorlist[i]) / 2)])
        pass

    # 各部分について構成候補を出す
    def innersearch(comlete_, candidator_, rest_):
        pass

    concrete_candidatelist = []
    for i in range(4):
        #concrete_candidatelist.append(innersearch([], candidator_combination[i], colorlist[i]))
        pass

    print()





if __name__ == '__main__':

    #machi("9m9m9m4p0p6p9p9p4s5s5s6s6s", [])

    tile_table = ["1m","2m","3m","4m","5m", "6m","7m","8m","9m",
                    "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
                    "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
                    "1z", "2z", "3z", "4z", "5z", "6z", "7z"]

    problemfile = open("p_normal_10000.txt")

    hand = ["(1p2p3p)", "(4p5p6p)", "[2z2z]", "7s8s", "(1s2s3s)"]
    naki = []
    agari = "9s"

    result = calculate_score_one(hand, naki, agari, True, False, "2z", "2z", 0, False, False, False, ["1m"])

    for line in problemfile:
        parts = line.split(" ")
        hand = ""
        for i in range(14):
            hand += tile_table[int(parts[i])]

        score = shanten(hand)