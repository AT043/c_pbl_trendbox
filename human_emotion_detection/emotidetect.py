import cv2
import os
import json
import requests
import shutil
import urllib.request
from deepface import DeepFace

def download_image(image_url, save_path):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
    else:
        print(f"❌ Gagal mengunduh {image_url}")

model_dir = "/app/models/"
os.makedirs(model_dir, exist_ok=True)

proto_url = "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt"
model_url = "https://github.com/chuanqi305/MobileNet-SSD/raw/master/mobilenet_iter_73000.caffemodel"

proto_file = os.path.join(model_dir, "deploy.prototxt")
model_file = os.path.join(model_dir, "mobilenet_iter_73000.caffemodel")

if not os.path.exists(proto_file):
    urllib.request.urlretrieve(proto_url, proto_file)

if not os.path.exists(model_file):
    urllib.request.urlretrieve(model_url, model_file)

net = cv2.dnn.readNetFromCaffe(proto_file, model_file)
class_names = {15: "person"}  # Kelas manusia pada MobileNet SSD

print("🔄 Mengecek gambar baru...")
backend_url = "http://spnj.my.id:8081/getimages"
response = requests.get(backend_url)

if response.status_code == 200:
    image_files = response.json().get("images", [])
else:
    print("❌ Gagal mengambil daftar gambar dari backend.")
    exit()

if not image_files:
    print("❌ Tidak ada gambar baru untuk diproses.")
    exit()

image_folder = "temp_images"
os.makedirs(image_folder, exist_ok=True)

image_paths = []
for image_name in image_files:
    image_url = f"http://spnj.my.id:8081/getimages/{image_name}"
    local_path = os.path.join(image_folder, image_name)
    download_image(image_url, local_path)
    image_paths.append(local_path)

results = []
for image_path in image_paths:
    image_name = os.path.basename(image_path)
    image = cv2.imread(image_path)

    height, width = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    people_count = sum(
        1 for i in range(detections.shape[2])
        if detections[0, 0, i, 2] > 0.5 and int(detections[0, 0, i, 1]) == 15
    )

    try:
        analysis_result = DeepFace.analyze(image_path, actions=['emotion'], enforce_detection=False)
        dominant_emotion = analysis_result[0]['dominant_emotion'] if analysis_result else "Unknown"
    except Exception as e:
        dominant_emotion = "Error"
        print(f"❌ Error saat mendeteksi emosi pada {image_name}: {e}")

    results.append({
        "image": image_name,
        "people_count": people_count,
        "dominant_emotion": dominant_emotion
    })

output_json = "detection_results.json"
with open(output_json, "w") as json_file:
    json.dump(results, json_file, indent=4)

print(f"✅ Deteksi selesai! Hasil disimpan dalam '{output_json}'")

shutil.rmtree(image_folder, ignore_errors=True)
print("🎯 Program selesai.")
