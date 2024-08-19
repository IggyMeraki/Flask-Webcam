import cv2
import numpy as np
import subprocess
from flask import Flask, Response, render_template, request

app = Flask(__name__)

# 计算摄像头数量
num_cameras = 0
while True:
    camera = cv2.VideoCapture(num_cameras)
    if not camera.isOpened():
        break
    else:
        camera.release()
        num_cameras += 1

def generate_frames(camera, max_width, max_height):
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            (h, w) = frame.shape[:2]
            aspect_ratio = w / h
            if w > max_width or h > max_height:
                if (max_width / max_height) > aspect_ratio:
                    new_height = max_height
                    new_width = int(max_height * aspect_ratio)
                else:
                    new_width = max_width
                    new_height = int(max_width / aspect_ratio)
                frame = cv2.resize(frame, (new_width, new_height))
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def generate_audio_stream():
    # 使用 arecord 命令录制音频
    cmd = [
        'arecord',
        '-D', 'hw:1,0',  # 使用设备 hw:1,0
        '-f', 'S16_LE',  # 设置格式
        '-r', '16000',   # 设置采样率
        '-c', '1',       # 设置通道数
        '-t', 'wav'      # 输出格式
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        while True:
            audio_chunk = process.stdout.read(512)
            if not audio_chunk:
                break
            yield audio_chunk
    finally:
        process.stdout.close()
        process.stderr.close()

@app.route('/')
def index():
    return render_template('index.html', num_cameras=num_cameras)

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    max_width = int(request.args.get('width', 640))
    max_height = int(request.args.get('height', 480))
    camera = cv2.VideoCapture(camera_id)
    return Response(generate_frames(camera, max_width, max_height), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_feed')
def audio_feed():
    return Response(generate_audio_stream(), mimetype='audio/wav')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
