from libs.funs.db_schema import tts, cfg, app, db, type2name, gramma2type, name2type, TTS_getRootDir, TTS_getDir4Type, TTS_getFullDir4TTSObj, my_dump, TTS_getCountByType
from blinker import signal
from datetime import datetime
from sqlalchemy import and_
import paho.mqtt.client as mqtt
import time
import subprocess
import re

import random
import asyncio
import logging

#import libs.classes.Reg_c as Reg_c
import libs.classes.Reg4vars_c as Reg4vars_c
import libs.classes.var_c as var_c
import libs.classes.Cmnd_c as Cmnd_c

ID_ERROR = 129

map_days = {'0': 100,  # poniedzialek
            '1': 101,  # wtorek
            '2': 102,  # sroda
            '3': 103,  # czwartek
            '4': 104,  # piatek
            '5': 105,  # sobota
            '6': 106}  # niedziela

map_months = {
    '1': 130,  # stycznia
    '2': 131,  # lutego
    '3': 132,
    '4': 133,
    '5': 134,
    '6': 135,
    '7': 136,
    '8': 137,
    '9': 138,
    '10': 139,
    '11': 140,
    '12': 141}


########################################


def playNativeSample(msg_num):
    obj = db.session.query(tts).filter(tts.id == msg_num).first()
   # print("Playing msg: %s"%( TTS_getFullDir4TTSObj(obj)))
    if obj:
        subprocess.Popen(['mpg123', '-r 48000', '-q',
                          TTS_getFullDir4TTSObj(obj)]).wait()


def playToken(token, REG):
    logging.info(f"Playing token '{token}'")

    # is simple SAY-type message
    if re.search(r"^SAY_(.+)$", token):
        if False == REG.is_stored(token):
            playNativeSample(ID_ERROR)
        else:
            logging.debug(
                f" found token={token}:v={REG.get_var(token).get_value()}")
            playNativeSample(REG.get_var(token).get_value())
        return
    if not REG.is_stored(token):
        logging.warning(f"WARN: Playing of token {token} failed!")
        return

    # getting variable
    var = REG.get_var(token)
    v = int(var.get_value())
    gramma = gramma2type(var.get_gramma())

    list = []
    is_minus = v < 0
    if is_minus:
        v = -v
        list.append(780)  # 780 is 'minus' text
    atLeastOne = False
    if v >= 1000:
        v1000 = v - (v % 100)
        t_1000 = db.session.query(tts).\
            filter(tts.var == v1000).\
            filter(tts.type == name2type('Compound')).\
            filter(tts.grama == gramma).\
            first()
        list.append(t_1000.id)
        v -= v1000
        atLeastOne = True
    if v >= 100:
        v100 = v - (v % 100)
        t_100 = db.session.query(tts).\
            filter(tts.var == v100).\
            filter(tts.type == name2type('Compound')).\
            filter(tts.grama == gramma).\
            first()
        list.append(t_100.id)
        v -= v100
        atLeastOne = True
    if v >= 20:
        v10 = v - (v % 10)
        t_10 = db.session.query(tts).\
            filter(tts.var == v10).\
            filter(tts.type == name2type('Compound')).\
            filter(tts.grama == gramma).\
            first()
        list.append(t_10.id)
        v -= v10
        atLeastOne = True
    if v > 0 or atLeastOne == False:
        t_1 = db.session.query(tts).\
            filter(tts.var == v).\
            filter(tts.type == name2type('Compound')).\
            filter(tts.grama == gramma).\
            first()
        list.append(t_1.id)
        v -= v
    logging.debug( f" Playing: '{list}'")
    for x in list:
        playNativeSample(x)


def playTemplate(msg_num, REG):
    obj = db.session.query(tts).filter(tts.id == msg_num).first()
    # subobjs = db.session.query(tts).filter(tts.ent==msg_num).all()
    if None != obj.structure:
        # print(obj.structure)
        for x in re.split(r',', obj.structure):
            token = re.search(r"%([^%]+)%$", x)
            if token:
                playToken(token.group(1), REG)
            else:
                playNativeSample(x)
        time.sleep(1500 / 1000)


def handleSay(msg_num):
    obj = db.session.query(tts).filter(tts.id == msg_num).first()
    if obj.type == name2type('Template'):  # not template
        playTemplate(msg_num)
    else:
        playNativeSample(msg_num)
    obj.played_count += 1
    db.session.commit()

def handleType(type_name, extra_id, repeats):
    while repeats >= 1:
        count = TTS_getCountByType(type_name)
        if count > 1:
            count /= 3  # since later will be sorted by played_count
            count = int(count)
            number = random.randrange(count)
        else:
            number = 0
        print("Loop: %d, Type: %s, Count=%d" % (repeats, type_name, count))
        print("number=%d" % number)
        obj = db.session.query(tts).\
            filter(tts.state == 1).\
            filter(tts.type == name2type(type_name)).\
            order_by(tts.played_count).\
            slice(number, 1).\
            first()
        if extra_id != -1:
            handleSay(extra_id)
            time.sleep(2)  # 1sec
        handleSay(obj.id)
        repeats -= 1
        if repeats > 0:
            time.sleep(2)

# if __name__ == "__main__":
#     # logging setup

