from db_schema import tts, cfg, app, db, type2name, gramma2type, name2type, TTS_getRootDir, TTS_getDir4Type, TTS_getFullDir4TTSObj, my_dump, TTS_getCountByType
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
import argparse

import libs.classes.Reg4vars_c as Reg4vars_c
import libs.classes.Reg4Commands_c as Reg4Commands_c
import libs.classes.Reg4Events_c as Reg4Events_c
import libs.classes.Reg4Listeners_c as Reg4Listeners_c

import libs.classes.var_c as var_c
import libs.classes.Cmnd_c as Cmnd_c
import libs.classes.Event_c as Event_c

import libs.funs.player as player


KUCHNIA_PODLOGA_SLOT_IN_MINS = 30
BRAMA_SLOT_IN_MINS_DEBUG = 1
BRAMA_SLOT_IN_MINS_NORMAL = 15
TIMER_15MINS = 15

GATE_LOC = r'prefix/brama/sensors/bin_in/0'

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
broker_address = "TODO: ip address of your broker"
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
format = "%(asctime)s_%(levelname)s:  %(message)s"
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


# following code just creates placeholders for data
REG = Reg4vars_c.Reg4vars_c()
REG.add(var_c.var_c('TEMP_CONTROL_BRAMA',
                    Event_c.Inputs.TEMP_SYSTEM,
                    'prefix/brama/sensors/T/values/0', 'MajorQuant', False))
REG.add(var_c.var_c('TEMP_OUTSIDE',
                    Event_c.Inputs.TEMP_OUTSIDE,
                    'prefix/brama/sensors/T/values/1', 'MajorQuant', False, -1))
REG.add(var_c.var_c('TEMP_KITCHEN_MATA',
                    Event_c.Inputs.TEMP_HEATING,
                    'prefix/kitchen/sensors/T/values/mata', 'MajorQuant', False))
REG.add(var_c.var_c('TEMP_KIDS_MATA',
                    Event_c.Inputs.TEMP_HEATING,
                    'prefix/bathroomZ/sensors/T/values/mata', 'MajorQuant'))
REG.add(var_c.var_c('TEMP_ATTIC_HOT_WATER_SENT',
                    Event_c.Inputs.TEMP_WATER,
                    'prefix/attic/sensors/T/values/0', 'MajorQuant', False))
REG.add(var_c.var_c('TEMP_ATTIC_CO_HEATING_SENT',
                    Event_c.Inputs.TEMP_HEATING,
                    'prefix/attic/sensors/T/values/6', 'MajorQuant', False))
REG.add(var_c.var_c('TEMP_ATTIC_CO_HEATING_RET',
                    Event_c.Inputs.TEMP_HEATING,
                    'prefix/attic/sensors/T/values/1', 'MajorQuant', False))


REG.add(var_c.var_c('FEMALE_QUANT_HOUR',
                    Event_c.Inputs.TIME_HOUR, None, 'FemOrderQuant'))
REG.add(var_c.var_c('MALE_QUANT_DAY',
                    Event_c.Inputs.TIME_DAY_OF_WEEK, None, 'MaleOrderQuant'))
REG.add(var_c.var_c('YEAR', Event_c.Inputs.TIME_YEAR, None, 'MaleOrderQuant'))
REG.add(var_c.var_c('MONTH', Event_c.Inputs.TIME_MONTH, None, 'MaleOrderQuant'))
REG.add(var_c.var_c('DAY', Event_c.Inputs.TIME_DAY, None, 'MaleOrderQuant'))
REG.add(var_c.var_c('HOUR', Event_c.Inputs.TIME_HOUR, None, 'FemOrderQuant'))
REG.add(var_c.var_c('MINUTE', Event_c.Inputs.TIME_MINUTE, None, 'MajorQuant'))
REG.add(var_c.var_c('SECOND', Event_c.Inputs.TIME_SECOND, None, 'MajorQuant'))
REG.add(var_c.var_c('GATE_OPENED_IN_MINUTES',
                    Event_c.Inputs.TIME_INTERVAL, None, 'MajorQuant'))
REG.add(var_c.var_c('SAY_DAY_NAME_CURRENT',
                    Event_c.Inputs.UNKNOWN, None, 'any'))
REG.add(var_c.var_c('SAY_MONTH', Event_c.Inputs.UNKNOWN, None, 'any'))
REG.add(var_c.var_c('SAY_RPI_KITCHEN_UPTIME',
                    Event_c.Inputs.UNKNOWN, None, 'any'))
REG.add(var_c.var_c('SAY_NET_DEVS_LAST_SEEN',
                    Event_c.Inputs.UNKNOWN, None, 'any'))
# used for keeping timer value
REG.add(var_c.var_c('TIMER_CURRENT_VALUE',
                    Event_c.Inputs.UNKNOWN, None, 'any'))


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
    client.publish("prefix/kitchen/control/commands", "P200005M1")

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
        client.publish("prefix/kitchen/control/commands", cmnd)


def my_kitchen_white_button_pressed(*args):
    cmd = args[0]

    var = REG.get_var('TIMER_CURRENT_VALUE')
    is_already_ongoing = var.is_first_time()

    logging.debug(f"White button pressed")


def my_attic_pir_triggered(*args):
    logging.debug(f"PIR triggered in Attic")


def my_kitchen_red_button_pressed(*args):
    client.publish("prefix/kitchen/control/commands", "P200005M1")

    logging.debug(f"red button pressed")


def my_bathroomZ_button2_triggered_opened(*args):
    client.publish("prefix/bathroomZ/control/commands", "L00FFFFFF5M1")
    logging.debug(f"Turning LED on")


def my_bathroomZ_button2_triggered_closed(*args):
    client.publish("prefix/bathroomZ/control/commands", "L00FFFFFF0M1")
    logging.debug(f"Turning LED on")


def my_bathroomZ_button1_triggered_new_colour(*args):
    client.publish("prefix/bathroomZ/control/commands", "L601M1")
    logging.debug(f"Changing just colour for a next one")


# MQTT instantiation
mqtt.Client.connected_flag = False
client = mqtt.Client("PI_Kitchen")  # create new instance

# Reg4Listeners, like virtual paths
Reg4Listeners = Reg4Listeners_c.Reg4Listeners_c(client, logging)
Reg4Listeners.addConfig('TODO: PATH_1')
Reg4Listeners.addConfig('TODO: PATH_2')
Reg4Listeners.addConfig('TODO: PATH_3')

# reg4events for processing by some heuristics
Reg4Events = Reg4Events_c.Reg4Events_c()

# reg4events for commands, like SAY... sth
Reg4Commands = Reg4Commands_c.Reg4Commands_c()
loc = r'prefix/kitchen/control/commands'
cmnd_mata_on = Cmnd_c.Cmnd_c('78', my_podloga_kitch_on,
                             KUCHNIA_PODLOGA_SLOT_IN_MINS, 1)
cmnd_mata_off = Cmnd_c.Cmnd_c('79', my_podloga_kitch_off, 0, 1)

cmnd1 = Cmnd_c.Cmnd_c(3, my_brama_open, brama_slot_length_in_mins * 60, 5)
cmnd2 = Cmnd_c.Cmnd_c(4, my_brama_close, 1, 1)
Reg4Commands.add_action(GATE_LOC, cmnd1, 'OPENED')
Reg4Commands.add_action(GATE_LOC, cmnd2, 'CLOSED')

# bathroomZ
loc = r'prefix/kitchen/sensors/bin_in/4'
cmnd = Cmnd_c.Cmnd_c(None, my_kitchen_pir_triggered, 0, 1)
Reg4Commands.add_action(loc, cmnd, 'OPENED')

loc = r'prefix/kitchen/sensors/bin_in/0'  # bialy, dodanie 10min to timera
cmnd = Cmnd_c.Cmnd_c(781, my_kitchen_white_button_pressed, 0, 1)
Reg4Commands.add_action(loc, cmnd, 'OPENED')

loc = r'prefix/kitchen/sensors/bin_in/2'  # czerwony
cmnd = Cmnd_c.Cmnd_c(None, my_kitchen_red_button_pressed, 0, 1)
Reg4Commands.add_action(loc, cmnd, 'OPENED')

# bathroomZ
loc = r'prefix/bathroomZ/sensors/bin_in/0'
cmnd_opened = Cmnd_c.Cmnd_c(None, my_bathroomZ_button2_triggered_opened, 0, 1)
cmnd_closed = Cmnd_c.Cmnd_c(None, my_bathroomZ_button2_triggered_closed, 0, 1)
Reg4Commands.add_action(loc, cmnd_opened, 'OPENED')
Reg4Commands.add_action(loc, cmnd_closed, 'CLOSED')

loc = r'prefix/bathroomZ/sensors/bin_in/1'
cmnd_new_colour = Cmnd_c.Cmnd_c(
    None, my_bathroomZ_button1_triggered_new_colour, 0, 1)
Reg4Commands.add_action(loc, cmnd_new_colour, 'OPENED')
Reg4Commands.add_action(loc, cmnd_new_colour, 'CLOSED')

loc = r'prefix/attic/sensors/bin_in/1'  # PIR triggered
cmnd = Cmnd_c.Cmnd_c(None, my_attic_pir_triggered, 0, 1)
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
        logging.info("Connected with result code "+str(rc))
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


def processReg4Listeners(msg_d):
    # processsing
    if True == Reg4Listeners.processEvent(msg_d['topic'], msg_d['command']):
        logging.info(f'Listener reacted to: {msg_d}')
        return True
    return False


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

        # handling commands like SAY, SAY_MATH etc
        if True == handle_say_message(msg):
            return

        # is topic being tracked for a value?
        if REG.is_tracked(message.topic):
            var = REG.get_tracked_var(message.topic)
            var.set_value(int(float(msg_d['command'])))
            if var.get_debug():
                logging.info(
                    f" {var.get_name()} update to {REG.get_var(var.get_name()).get_value()}")
            # even though it might have been processed in tracking, another action might have been
            # scheduled for this location, so not breaking, just continuing

            # events handling for "smartnest"
            Reg4Events.add_event(var)

        # normal processing
        if False == processReg4Commands(msg_d):
            processReg4Listeners(msg_d)

    except ValueError:
        player.playNativeSample(ID_ERROR)
        logging.warning("Oops!  That was no valid number.  Try again...")


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
    client.loop_start()

    while True:
        try:
            client.connect(broker_address, 1883)  # connect to broker
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
