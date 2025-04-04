import cv2
import os
import time
from datetime import datetime
from flask import Flask, Response, render_template, jsonify
from PIL import Image
import piexif
import requests  # Tambahkan import requests

app = Flask(__name__)

proto_url = "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt"
model_url = "https://github.com/chuanqi305/MobileNet-SSD/raw/master/mobilenet_iter_73000.caffemodel"

proto_file = os.path.join(model_dir, "deploy.prototxt")
model_file = os.path.join(model_dir, "mobilenet_iter_73000.caffemodel")
net = cv2.dnn.readNetFromCaffe(proto_file, model_file)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

CLOUD_API_URL = "http://spnj.my.id:8081/upload"

output_folder = "captured_images"
os.makedirs(output_folder, exist_ok=True)

cap = cv2.VideoCapture(1)
capture_interval = 10
last_capture_time = time.time()
last_image_filename = ""
is_capturing = True  

def generate_frames():
    global last_capture_time, last_image_filename, is_capturing
    while True:
        success, frame = cap.read()
        if not success:
            break

        if not is_capturing:  
            continue

        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, scalefactor=0.007843, size=(300, 300), mean=127.5)
        net.setInput(blob)
        detections = net.forward()

        humans = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                class_id = int(detections[0, 0, i, 1])
                if class_id == 15:
                    box = detections[0, 0, i, 3:7] * [w, h, w, h]
                    (x, y, x2, y2) = box.astype("int")
                    humans.append((x, y, x2 - x, y2 - y))
                    cv2.rectangle(frame, (x, y), (x2, y2), (255, 0, 0), 2)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50))

        for (fx, fy, fw, fh) in faces:
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 255, 0), 2)

        if len(humans) > 0 and time.time() - last_capture_time > capture_interval:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            last_image_filename = f"capture_{timestamp}.jpg"
            image_path = os.path.join(output_folder, last_image_filename)

            cv2.imwrite(image_path, frame)

            label = "Wajah Terdeteksi" if len(faces) > 0 else "Wajah Tidak Terdeteksi"
            image = Image.open(image_path)

            exif_dict = {"0th": {piexif.ImageIFD.ImageDescription: label.encode("utf-8")}}
            exif_bytes = piexif.dump(exif_dict)
            image.save(image_path, exif=exif_bytes)

            print(f"Gambar disimpan: {last_image_filename} | Label: {label}")
            last_capture_time = time.time()

            # Kirim gambar ke cloud dengan error handling
            try:
                with open(image_path, "rb") as img_file:
                    response = requests.post(CLOUD_API_URL, files={"image": img_file})
                    response.raise_for_status()  # Pastikan tidak ada error HTTP
                    print(f"Gambar berhasil dikirim: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Gagal mengirim gambar: {e}")

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/last_capture')
def last_capture():
    return jsonify({"filename": last_image_filename})

@app.route('/check_new_capture')
def check_new_capture():
    return jsonify({"filename": last_image_filename})

@app.route('/start_capture', methods=['POST'])
def start_capture():
    global is_capturing
    is_capturing = True
    return jsonify({"status": "Capturing started"})

@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    global is_capturing
    is_capturing = False
    return jsonify({"status": "Capturing stopped"})

if __name__ == '__main__':
    app.run(debug=True)
