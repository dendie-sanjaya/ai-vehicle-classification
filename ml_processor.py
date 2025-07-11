import os
from ultralytics import YOLO
import json

class MLProcessor:
    def __init__(self, model_name='yolov8x.pt'): # <--- Default ke yolov8x.pt
        try:
            self.model = YOLO(model_name)
            print(f"Model YOLOv8 ({model_name}) berhasil dimuat.")
        except Exception as e:
            raise RuntimeError(f"Gagal memuat model YOLOv8 {model_name}: {e}")

        # Kelas-kelas COCO yang relevan untuk deteksi kendaraan
        self.vehicle_classes = {
            # COCO dataset class IDs and names:
            2: 'car',
            3: 'motorcycle'
        }
        
        # Ambang batas deteksi kelas untuk lalu lintas
        self.traffic_thresholds = {
            'low': (0, 15),     # 0-15 kendaraan
            'medium': (16, 40), # 16-40 kendaraan
            'heavy': (41, 100), # 41-100 kendaraan
            'extreme': (101, float('inf')) # >100 kendaraan
        }

    def preprocess_image(self, image_path):
        """
        Melakukan pra-pemrosesan gambar (jika diperlukan oleh model).
        Untuk YOLOv8, input path langsung sudah cukup.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Gambar tidak ditemukan di: {image_path}")
        return image_path

    def predict_traffic(self, processed_image_path):
        """
        Melakukan prediksi objek pada gambar menggunakan model YOLOv8.
        Mengembalikan objek Results dari Ultralytics.
        """
        # conf=0.25 adalah ambang batas keyakinan. Turunkan jika ingin mendeteksi objek
        # dengan keyakinan lebih rendah (bisa meningkatkan false positives).
        # iou=0.7 adalah ambang batas Intersection Over Union untuk Non-Maximum Suppression.
        # Untuk lalu lintas yang sangat padat, bisa sedikit diturunkan (misal 0.5-0.7)
        # jika deteksi yang tumpang tindih menjadi masalah dan Anda ingin menangkap lebih banyak.
        results = self.model.predict(processed_image_path, conf=0.0002, iou=0.1, verbose=False)
        return results # Ini adalah list of Results objects

    def extract_and_classify_results(self, ml_raw_results):
        """
        Mengekstrak, mengklasifikasikan, dan menghitung hasil deteksi.
        """
        total_num_vehicles = 0
        vehicle_counts = {v_name: 0 for v_name in self.vehicle_classes.values()}
        
        raw_output_list = []

        # ml_raw_results adalah list of Results objects, biasanya hanya ada satu untuk satu gambar
        for r in ml_raw_results:
            boxes = r.boxes.cpu().numpy() # Dapatkan bounding boxes, pindahkan ke CPU jika di GPU
            
            # Simpan output mentah untuk debugging atau analisis lebih lanjut
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist() # [x1, y1, x2, y2]
                raw_output_list.append({
                    'class_id': cls,
                    'class_name': self.model.names[cls],
                    'confidence': conf,
                    'bbox': [round(val, 2) for val in xyxy] # Bulatkan untuk penyimpanan
                })

            for cls in boxes.cls:
                class_id = int(cls)
                if class_id in self.vehicle_classes:
                    vehicle_type = self.vehicle_classes[class_id]
                    vehicle_counts[vehicle_type] += 1
                    total_num_vehicles += 1
        
        # Tentukan tingkat lalu lintas
        traffic_level = "unknown"
        for level, (min_val, max_val) in self.traffic_thresholds.items():
            if min_val <= total_num_vehicles <= max_val:
                traffic_level = level
                break

        return {
            'total_num_vehicles': total_num_vehicles,
            'traffic_level': traffic_level,
            'vehicle_types_json': json.dumps(vehicle_counts), # Simpan sebagai JSON string
            'raw_ml_output': json.dumps(raw_output_list) # Simpan output mentah sebagai JSON string
        }