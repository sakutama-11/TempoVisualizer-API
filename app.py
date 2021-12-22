import sys
import os
os.environ['NUMBA_CACHE_DIR'] = '/tmp/'
import subprocess
import boto3
import numpy as np
import json
import re
import math
from pathlib import Path
import base64
import librosa as lr
import colorsys
import cv2
bucket = os.environ['AWS_S3_BUCKET']

def get_filename_from_body(str):
    # filename=\"filename\"を切り出し
    p = r'filename=.*"'
    r = re.findall(p, str)  # ['filename="testmusic.mp3"']
    str = r[0]  # 'filename="testmusic.mp3"'
    filename = str.split('"')[1]  # ['filename=', 'testmusic.mp3', '']
    return filename


def save_posted_musicfile(body):
    # バイナリがBase64にエンコードされているので、ここでデコード
    music_base64 = base64.b64decode(body['base64'])
    filename = body['filename']
    fw = open('/tmp/' + filename, 'wb')
    fw.write(music_base64)
    return filename


def download_from_s3(key, filename, tmp_path):
    s3_client = boto3.client('s3')
    download_path = tmp_path + filename
    s3_client.download_file(bucket, key, download_path)


def upload_to_s3(img, filename, tmp_path):
    s3_client = boto3.client('s3')

    ret = cv2.imwrite(tmp_path + filename, img)
    img_key = 'public/img/' + filename
    s3_client.upload_file(tmp_path + filename, bucket, img_key)


def encode_to_base64(img):
    result, dst_data = cv2.imencode('.png', img)
    image_base64 = base64.b64encode(dst_data)
    image_str = image_base64.decode('utf-8')
    return image_str


def handler(event, context):
    music_filename = event['filename']
    key = event['key']
    tmp_dir = '/tmp/'
    download_from_s3(key, music_filename, tmp_dir)
    # music_filename = save_posted_musicfile(key, tmp_dir)
    image_filename = os.path.splitext(music_filename)[0] + '.png'

    tempo, beats = analyze_tempo(tmp_dir + music_filename)

    arr_tempo, beat_time = spline_by_mean_between_frames(tempo, beats, 4)

    img = create_image_from_tempo(beats, beat_time, tempo, arr_tempo)
    # image_str = encode_to_base64(img)
    # return json.dumps({
    #     "image_name": image_filename,
    #     "base64": image_str,
    # })
    upload_to_s3(img, image_filename, tmp_dir)
    return json.dumps({
        "image_name": image_filename
    })


def avg_tempo(arr_sec, idx, range):
    avg_tempo = 60 / ((arr_sec[idx + range] - arr_sec[idx]) / range)
    return int(avg_tempo)


def analyze_tempo(music_filename):
    path = Path(music_filename)
    y, sr = lr.load(path)
    tempo, beats = lr.beat.beat_track(y=y, sr=sr)
    return tempo, beats


def spline_by_mean_between_frames(tempo, beats, avg_range):
    # フレーム間の秒数を配列にする
    beat_time = lr.frames_to_time(beats)
    # 平均テンポの配列の0項目に加える
    arr_tempo = []
    avg_range = 4
    for i in range(len(beat_time) - avg_range):
        arr_tempo = np.append(arr_tempo, avg_tempo(beat_time, i, avg_range))

    # 最初に2フレーム、最後に2フレーム平均テンポを加える(beats配列とサイズが同じになるはず)
    arr_tempo = np.append([tempo, tempo], arr_tempo)
    arr_tempo = np.append(arr_tempo, [tempo, tempo])
    return arr_tempo, beat_time


def create_image_from_tempo(beats, beat_time, tempo, arr_tempo):
    height = len(beats) * 4 // 10
    width = len(beats) * 4
    src = np.zeros((height, width, 3))
    for i in range(len(beat_time) - 1):
        # 塗りつぶす幅を計算
        start = round(beat_time[i] * width / beat_time[-1])
        pixel = round((beat_time[i + 1] - beat_time[i]) * width / beat_time[-1])
        # arr_tempoとtmpoの差に応じて色相を指定
        # bpm差 1で8色相変化
        hue = (tempo - arr_tempo[i]) * -6 + 60
        hue = max(hue, 0)
        hue = min(240, hue)
        hue = float(hue) / 180
        rgb_0_to_1 = colorsys.hsv_to_rgb(hue, 1, 1)
        rgb = [n * 255 for n in rgb_0_to_1]
        # 塗りつぶす
        src[:, start:start + pixel, 0:3] = rgb

    # 画像作る
    img = cv2.cvtColor(src.astype(np.float32), cv2.COLOR_BGR2RGB)
    return img


# if __name__ == '__main__':
#     # music_filename = sys.argv[1]
#     music_filename = "Take_Action.mp3"
#     image_filename = os.path.splitext(music_filename)[0] + '.png'

#     tempo, beats = analyze_tempo(music_filename)

#     arr_tempo, beat_time = spline_by_mean_between_frames(tempo, beats, 4)

#     img = create_image_from_tempo(beats, beat_time, tempo, arr_tempo)
#     ret = cv2.imwrite('./storage/image/' + image_filename, img)
#     assert ret, 'failed'
#     print(image_filename)
