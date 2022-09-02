
from blinker import signal
from datetime import datetime
from sqlalchemy import and_
import paho.mqtt.client as mqtt

import time
import subprocess
import re
import os
import random
import asyncio
import logging
import argparse
import signal

from libs.funs.db_schema import tts, db, name2type, TTS_getCountByType
import libs.funs.player as player

import libs.classes.Reg4vars_c as Reg4vars_c
import libs.classes.Reg4Commands_c as Reg4Commands_c
import libs.classes.Reg4Events_c as Reg4Events_c
import libs.classes.Reg4Listeners_c as Reg4Listeners_m
import libs.classes.Reg4Configs_c as Reg4Configs_m
import libs.classes.Cmnd_c as Cmnd_c
import libs.classes.Event_c as Event_c


KUCHNIA_PODLOGA_SLOT_IN_MINS = 30
BRAMA_SLOT_IN_MINS_DEBUG = 1
BRAMA_SLOT_IN_MINS_NORMAL = 15
TIMER_15MINS = 15

PREFIX = ''

GATE_LOC = f'{PREFIX}ard/brama/sensors/bin_in/0'

ID_ERROR_L3_NET_NO_GOOGLE = 665
ID_ERROR_L2_NET_NO_ISP_EXT_ROOTER = 664
ID_ERROR_L1_NET_NO_ISP_ACCESS_POINT = 663
ID_ERROR_L0_NET_NO_LAN_ROUTER = 666
ID_ERROR_L0_NET_IS_OK_NOW = 775
_ID = 0
_FUN = 1

CFG_WITH_AUDIO = True

# The broker configuration
# broker_address="iot.eclipse.org"
broker_address = os.environ.get("HOMEATIC_IP_BROKER")
if not broker_address:
    raise Exception(
        "Broker address must be defined with the 'HOMEATIC_IP_BROKER' environmental variable.")
broker_main_topic = "#"

# the arguments parser
ap = argparse.ArgumentParser(description='Args parsing')

# Arguments parsing
ap.add_argument("-d", "--debug", required=False,
                help="Debug level")
args = vars(ap.parse_args())
debug_level = args['debug']

# debugging
if not debug_level:
    debug_level_numeric = logging.WARNING
    brama_slot_length_in_mins = BRAMA_SLOT_IN_MINS_NORMAL
else:
    debug_level_numeric = logging._nameToLevel[debug_level]
    # for debugging, slot is set to 1min
    brama_slot_length_in_mins = BRAMA_SLOT_IN_MINS_DEBUG
    CFG_WITH_AUDIO = False

# logging setup
format = "%(asctime)s_%(levelname)s_%(threadName)s:  %(message)s"
logging.basicConfig(format=format, level=debug_level_numeric,
                    datefmt="%H:%M:%S")  # filename='example.log',
logging.info("Main: creating new instance of MQTT listener")


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    command = ['ping', '-c', '2', '-W', '5', host]

    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


last_notification = 0
def detect_access():
    now = datetime.now()
    day_num = now.weekday()
    global last_notification

    if day_num >= 5:  # Fri is 4
        return

    if now.hour < 7 or now.hour > 17:  # only office hours
        last_notification = 0
        return

    HOSTS = Reg4Configs_m.Reg4Configs_c.getInstance().getConfig('hosts')

    notify = -1
    if False == ping(HOSTS['L3']):
        if False == ping(HOSTS['L2']):
            if False == ping(HOSTS['L1']):
                if False == ping(HOSTS['L0']):
                    notify = ID_ERROR_L0_NET_NO_LAN_ROUTER
                else:
                    notify = ID_ERROR_L1_NET_NO_ISP_ACCESS_POINT
            else:
                notify = ID_ERROR_L2_NET_NO_ISP_EXT_ROOTER
        else:
            notify = ID_ERROR_L3_NET_NO_GOOGLE

    if -1 != notify:
        if int(now.timestamp()) - last_notification > 60:
            logging.warning(f'INET: no access to Internet {notify}')
            last_notification = int(now.timestamp())
            player.playNativeSample(notify)
    else:
        if 0 != last_notification:
            player.playNativeSample(ID_ERROR_L0_NET_IS_OK_NOW)
            last_notification = 0


def handle_pdb(sig, frame):
    import pdb
    pdb.Pdb().set_trace(frame)


# following code just creates placeholders for data
REG = Reg4vars_c.Reg4vars_c()
REG.addConfig(
    'vars', env_var_with_filename='HOMEATIC_PATH_CFG_VARS')
REG.InstantiateVars('vars')


def my_podloga_kitch_on(*args):
    handleSample("83")  # RaportTemperaturaKuchniaPodloga


def my_podloga_kitch_off(*args):
    handleSample("83")  # RaportTemperaturaKuchniaPodloga


def my_timer_15m_start(cfg_list):
    handleSample("659")
    if cfg_list[1][0] > 0:
        handleSample("656")
    else:
        handleSample("655")
    relaunch(cfg_list, 1)


def my_brama_open(*args):
    cmnd = args[0]

    current_value = REG.get_var(
        'GATE_OPENED_IN_MINUTES').add_to_value(brama_slot_length_in_mins)

    if cmnd.is_last_run():
        handleSample("5")  # BramaGarazOstrzezenie
        REG.get_var('GATE_OPENED_IN_MINUTES').set_value(0)
    else:
        handleSample("15")  # BramaGarazOtwartaPrzez


def my_brama_close(*args):
    cmd = args[0]

    handleSample(cmd.get_sample_id())  # BramaGarazOtwarta

    # we want to get opened's cmnd
    cmnd_open = Reg4Commands.get_value(GATE_LOC, 'OPENED')
    if cmnd_open.is_still_running():
        cmnd_open.cancel_unblocking()

    REG.get_var('GATE_OPENED_IN_MINUTES').set_value(0)


def my_kitchen_pir_triggered(*args):
    now = datetime.now()
    # only office hours
    if now.hour < 6 or now.hour > 20:
        return

    try:
        var = REG.get_var('TEMP_OUTSIDE')
    except Exception as e:
        logging.debug(f"ERR: '{e.__cause__}'")
        return

    temp_outside = var.get_value()
    temp_out_min = -10
    temp_out_max = 8
    if temp_outside < temp_out_max:
        temp_outside_range = temp_out_max - temp_out_min
        temp_mate_min = 19
        temp_mate_max = 26
        temp_mate_range = temp_mate_max - temp_mate_min
        ratio = float(temp_out_max - temp_outside) / float(temp_outside_range)
        temp = int(temp_mate_min + (ratio * temp_mate_range))
        if temp > temp_mate_max:
            temp = temp_mate_max
        cmnd = f'H10{temp}{temp+1}5M1'  # H1024255M1
        client.publish(f"{PREFIX}ard/kitchen/control/commands", cmnd)


def my_kitchen_white_button_pressed(*args):
    cmd = args[0]

    var = REG.get_var('TIMER_CURRENT_VALUE')
    is_already_ongoing = var.is_first_time()

    logging.debug(f"White button pressed")


# MQTT instantiation
mqtt.Client.connected_flag = False
client = mqtt.Client("PI_Kitchen")  # create new instance


# Reg4Listeners, like virtual paths
Reg4Listeners = Reg4Listeners_m.Reg4Listeners_c(client, logging)
Reg4Listeners.addConfig(
    env_var_with_filename='HOMEATIC_PATH_CFG_GARDEN')
Reg4Listeners.addConfig(
    env_var_with_filename='HOMEATIC_PATH_CFG_BATHROOMZ')
Reg4Listeners.addConfig(
    env_var_with_filename='HOMEATIC_PATH_CFG_ATTIC')

Reg4Configs = Reg4Configs_m.Reg4Configs_c.getInstance()
Reg4Configs.addConfig(
    'hosts', env_var_with_filename='HOMEATIC_PATH_CFG_HOSTS')

# reg4events for processing by some heuristics
Reg4Events = Reg4Events_c.Reg4Events_c()

# reg4events for commands, like SAY... sth
Reg4Commands = Reg4Commands_c.Reg4Commands_c()
loc = f'{PREFIX}ard/kitchen/control/commands'
cmnd_mata_on = Cmnd_c.Cmnd_c('78', my_podloga_kitch_on,
                             KUCHNIA_PODLOGA_SLOT_IN_MINS, 1)
cmnd_mata_off = Cmnd_c.Cmnd_c('79', my_podloga_kitch_off, 0, 1)

cmnd1 = Cmnd_c.Cmnd_c(3, my_brama_open, brama_slot_length_in_mins * 60, 5)
cmnd2 = Cmnd_c.Cmnd_c(4, my_brama_close, 1, 1)
Reg4Commands.add_action(GATE_LOC, cmnd1, 'OPENED')
Reg4Commands.add_action(GATE_LOC, cmnd2, 'CLOSED')

# kitchen
loc = f'{PREFIX}ard/kitchen/sensors/bin_in/4'
cmnd = Cmnd_c.Cmnd_c(None, my_kitchen_pir_triggered, 0, 1)
Reg4Commands.add_action(loc, cmnd, 'OPENED')

loc = f'{PREFIX}ard/kitchen/sensors/bin_in/0'  # bialy, dodanie 10min to timera
cmnd = Cmnd_c.Cmnd_c(781, my_kitchen_white_button_pressed, 0, 1)
Reg4Commands.add_action(loc, cmnd, 'OPENED')


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


def local_say(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    print("Subscribing to topic", broker_main_topic)


def handleSample(msg_num):
    obj = db.session.query(tts).filter(tts.id == msg_num).first()
    if obj.type == name2type('Template'):  # not template
        player.playTemplate(msg_num, REG)
    else:
        player.playNativeSample(msg_num)
    obj.played_count += 1
    db.session.commit()


def on_connect(client, userdata, flags, rc):
    if 0x0 == rc:
        client.connected_flag = True
        logging.info(f"Connected with result code: {str(rc)}, flags={flags}")
        logging.info(f"Subscribing to topic: '{broker_main_topic}'")

        client.subscribe(broker_main_topic)
    else:
        logging.warn("Bad connection Returned code= ", rc)


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
            handleSample(extra_id)
            time.sleep(2)  # 1sec
        handleSample(obj.id)
        repeats -= 1
        if repeats > 0:
            time.sleep(2)


def processReg4Commands(msg_d):
    # processsing
    mqtt_path = msg_d['topic']
    if not mqtt_path in Reg4Commands._hTable:
        return False

    cmnd = None
    # for each command on given path
    for c in Reg4Commands._hTable[mqtt_path]:
        # ... we check matching
        groups = re.search(c, msg_d['command'])
        if groups:
            # if there is a match, we found a command
            cmnd = Reg4Commands._hTable[mqtt_path][c]
            break

    # have we found a command for given path?
    if not cmnd:
        logging.debug(
            f"We're tracing '{mqtt_path}', but not command '{msg_d['command']}' in Reg4Commands, ignoring")
        return True

    # ok, we've found, so we're tracking location, have command, so let's do the action
    if cmnd.get_sample_id():  # do we have callback set?
        if CFG_WITH_AUDIO:
            handleSample(cmnd.get_sample_id())

    # is commnans still running?
    if cmnd.get_fun():  # do we have callback set?
        if cmnd.is_still_running():
            cmnd.retrigger()
        else:
            cmnd.trigger()
    logging.info(f'Command reacted to: {msg_d}')
    return True


def processReg4Listeners(msg_d, with_topic=False):
    # topic check
    if True == with_topic:
        if True == Reg4Listeners.processEvent([msg_d['topic']]):
            logging.info(f'Listener reacted to: {msg_d}')

    # command check, here we can react to command + value pair
    if True == Reg4Listeners.processEvent([msg_d['topic'], msg_d['command']]):
        logging.info(f'Listener reacted to: {msg_d}')


def handle_say_message(msg):
    if re.search('^SAY#\\d+$', msg):
        # logging.warning(f'SAY_KEY: msg: *{msg}*')
        x = re.search('^SAY#(\\d+)$', msg)
        handleSample(x.group(1))
        return True
    if re.search('^SAY_RAND#JOKE', msg):
        count = re.search('^SAY_RAND#JOKE*(\\d+)$', msg)
        count = 1 if not count else int(count.group(1))
        handleType(u'JokeOfADay', 24, count)
        return True
    if re.search('^SAY_RAND#WISDOM', msg):
        count = re.search('^SAY_RAND#WISDOM\\*(\\d+)$', msg)
        count = 1 if not count else int(count.group(1))
        handleType(u'WordOfWisdom', 239, count)
        return True
    if re.search('^SAY_RAND#NEWS', msg):
        count = re.search('^SAY_RAND#NEWS*(\\d+)$', msg)
        count = 1 if not count else int(count.group(1))
        handleType(u"News", 244, count)
        return True
    if re.search('^SAY_RAND#MATH', msg):
        count = re.search('^SAY_RAND#MATH*(\\d+)$', msg)
        count = 1 if not count else int(count.group(1))
        handleType(u"Math", 480, count)
        return True
    if re.search('^SAY_RAND#SPANISH_WORD', msg):
        count = re.search('^SAY_RAND#SPANISH_WORD*(\\d+)$', msg)
        count = 1 if not count else int(count.group(1))
        handleType(u"SpanishPhrase", 246, count)
        return True
    if re.search('^SAY_RAND#GERMAN_WORD', msg):
        count = re.search('^SAY_RAND#GERMAN_WORD*(\\d+)$', msg)
        count = 1 if not count else int(count.group(1))
        handleType(u"GermanPhrase", 778, count)
        return True
    if re.search('^SAY_RAND#ENGLISH_WORD', msg):
        count = re.search('^SAY_RAND#ENGLISH_WORD*(\\d+)$', msg)
        count = 1 if not count else int(count.group(1))
        handleType(u"EnglishPhrase", 779, count)
        return True
    return False


def on_message(client, userdata, message):
    # print("message '%s', topic: '%s'"% (str(message.payload.decode("utf-8")), (str(message.topic))))
    try:
        msg = str(message.payload.decode("utf-8"))
        msg_d = {'command': msg, 'topic': str(message.topic)}

        # if getNumOfHandlers([msg_d['command']]) > 0:
        #     processHandlers([msg_d['command']])
        # if getNumOfHandlers([msg_d['topic'], msg_d['command']]) > 0:
        #     processHandlers([msg_d['command'], msg_d['command']])

        # Handlers:
        #  - say
        #  - inline actions (listeners to command and/or command + topic)
        #  - external actions (via json)
        #  - complicated functions

        # handling commands like SAY, SAY_MATH etc
        if re.search('/voice/salon', message.topic):
            if True == handle_say_message(msg_d['command']):
                return

        # is topic being tracked for a value?
        if REG.is_tracked(message.topic):
            # in given location we can have more than one var
            for var in REG.get_tracked_var_yield(message.topic):
                regex = var.get_key('regex')
                updated = False
                if regex:
                    x = re.search(regex, msg)
                    if x:
                        var.set_value(x.group(1))
                        updated = True
                    # else:
                    #     logging.debug(
                    #         f" Regex set to '{regex}', but no match in {var.get_name()}")
                else:
                    var.set_value(int(float(msg_d['command'])))
                    updated = True

                if updated and var.get_debug():
                    logging.info(
                        f" {var.get_name()} update to {REG.get_var(var.get_name()).get_value()}")
        #     # even though it might have been processed in tracking, another action might have been
        #     # scheduled for this location, so not breaking, just continuing

        #     # events handling for "smartnest"
        #     Reg4Events.add_event(var)

        # normal processing
        if False == processReg4Listeners(msg_d):
            processReg4Commands(msg_d)

    except ValueError:
        # player.playNativeSample(ID_ERROR)
        logging.warning(
            f"Oops!  That was no valid number. {ValueError.strerror} Try again...")


def on_log(client, userdata, level, buf):
    logging.info(" log: ", buf)


async def task_Periodic1m():
    while True:
        # print('task_Periodic1m')
        detect_access()
        await asyncio.sleep(60)


async def task_Periodic10s():
    while True:
        # print('task_Periodic10s')
        now = datetime.now()
        day_num = now.weekday()
        # print(str(day_num))
        # d1 = now.strftime("%d/%m/%Y %H:%M:%S")
        # print("d1 =", now.hour)
        # print("d1 =", now.year)
        REG.get_var('YEAR').set_value(now.year)
        REG.get_var('SAY_MONTH').set_value(map_months[str(now.month)])
        REG.get_var('MONTH').set_value(now.month)
        REG.get_var('MALE_QUANT_DAY').set_value(now.day)
        REG.get_var('DAY').set_value(now.day)
        REG.get_var('FEMALE_QUANT_HOUR').set_value(now.hour)
        REG.get_var('HOUR').set_value(now.hour)
        REG.get_var('MINUTE').set_value(now.minute)
        REG.get_var('SECOND').set_value(now.second)
        REG.get_var('SAY_DAY_NAME_CURRENT').set_value(map_days[str(day_num)])
        REG.get_var('MOD_MQTT_UPTIME_IN_DAYS')

        await asyncio.sleep(10)


async def task_Periodic1s():
    global client
    while True:
        client.loop()
        await asyncio.sleep(1)

if __name__ == "__main__":
    # MQTT setup
    client.on_message = on_message  # attach function to callback
    client.on_connect = on_connect
    mqttt_loop_started = False

    # debugger setup
    signal.signal(signal.SIGUSR1, handle_pdb)
    logging.info(
        f"My pid: '{os.getpid()}'")

    # main loop
    while True:
        try:
            client.connect(broker_address, 1883)  # connect to broker
            if not mqttt_loop_started:
                client.loop_start()
                mqttt_loop_started = True
            break
        except:
            logging.info(
                f"Problems with a connection to broker: '{broker_address}' (retry in 10s)")
        time.sleep(10)

    while False == client.connected_flag:  # wait in loop
        logging.info(f"Connecting to broker: '{broker_address}'")
        time.sleep(1)

    # asyncio section
    loop = asyncio.get_event_loop()
    # loop.call_later(5, stop)
    task_10s = loop.create_task(task_Periodic10s())
    task_1m = loop.create_task(task_Periodic1m())
    try:
        loop.run_until_complete(task_10s)
        loop.run_until_complete(task_1m)
    except asyncio.CancelledError as e:
        logging.error(e)
