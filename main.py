#!/usr/bin/env python3
# python3.7で動作確認済み

import ambient
import time
import json
import datetime as dt
import sys
import random
import os
import subprocess
import requests

def conv(data):
    if data[0] in {"temp", "hum"}:
        return int(data[1]) / 100
    else:
        return int(data[1])

def send_message(token,message):
    headers = {
        "Authorization": "Bearer " + token,
    }
    files = {
        "message": (None, message),
    }
    res = requests.post("https://notify-api.line.me/api/notify", headers=headers, files=files)
    print(res)

# 設定値読み込み
f = open("/home/pi/work/usb_notifier/config.json", "r")
conf = json.loads(f.read())
f.close()

data_dic = {}
data_l = []
for device in conf["devices"]:
    data_arr = []
    if "cpu_temp" == device["sensor_name"]:
        cmd = 'cat /sys/class/thermal/thermal_zone0/temp'
        data = int((subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        shell=True).communicate()[0]).decode('utf-8').split("\n")[0])/1000.0
        data_arr.append(str(data))
        data_dic[device["sensors"][0]] = data
    else:
        filename = conf["logdir"] + "/" + device["sensor_name"] + "/" + device["sensor_name"] + "_" + dt.datetime.now().strftime("%Y-%m-%d") + ".csv"
        try:
            f = open(filename,"r")
            # ログの末尾1行をとってくる
            lines = f.readlines()[-1:][0][:-1]
            f.close

            # ログに含まれるセンサの数がconfig.jsonと同じか確認
            data_list = lines.split(",")[1].split(";")
            data_num = (len(data_list) - 1)
            if len(device["sensors"]) == data_num:
                for i in range(data_num):
                    # センサ名と数字のペアができる ex) ["temp","2657"]
                    data_pair = data_list[i].split("=")

                    if data_pair[0] in device["sensors"]:
                        # 送信すべきambientのデータ番号が存在することを確認 ex) d1~d8
                        data_l.append(device["sensors"][data_pair[0]] + ":" + str(conv(data_pair)))
                        data_dic[device["sensors"][data_pair[0]]] = conv(data_pair)
                    else:
                        break
            else:
                break
        except Exception as e:
            pass

# 送信メッセージ作成
messages = conf["title"] + "\n"
for i in range(len(data_l)):
    messages += data_l[i] + "\n"
print(messages)

# line送信処理
send_message(conf["line_token"],messages)
