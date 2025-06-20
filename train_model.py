# train_knn.py - Latih model KNN dari dataset warna rata-rata

import os
import cv2
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import joblib

def extract_avg_color(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    avg_color = np.mean(image, axis=(0, 1))
    return avg_color.astype(int)

X_train = []
y_train = []

# Load gambar organik
organik_folder = "dataset/organik"
for img_file in os.listdir(organik_folder):
    path = os.path.join(organik_folder, img_file)
    color = extract_avg_color(path)
    if color is not None:
        X_train.append(color)
        y_train.append(0)  # Organik

# Load gambar anorganik
anorganik_folder = "dataset/anorganik"
for img_file in os.listdir(anorganik_folder):
    path = os.path.join(anorganik_folder, img_file)
    color = extract_avg_color(path)
    if color is not None:
        X_train.append(color)
        y_train.append(1)  # Anorganik

# Latih model KNN
model = KNeighborsClassifier(n_neighbors=3)
model.fit(X_train, y_train)

# Simpan model
joblib.dump(model, "model_knn.pkl")
print("✅ Model berhasil disimpan sebagai model_knn.pkl")
