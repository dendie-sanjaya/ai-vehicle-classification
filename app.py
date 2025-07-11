import os
import json
from ml_processor import MLProcessor
from database_manager import DatabaseManager

class TrafficAnalysisApp:
    def __init__(self, db_path='traffic_data.db', ml_model_name='yolov8x.pt'): # <--- Diubah ke yolov8x.pt
        self.db_manager = DatabaseManager(db_path)
        # Teruskan model_name ke MLProcessor. Pastikan model .pt sudah diunduh.
        self.ml_processor = MLProcessor(ml_model_name) 

    def run_analysis(self, image_path):
        """
        Menjalankan seluruh proses analisis untuk sebuah foto lalu lintas.
        """
        print(f"\n--- Memulai analisis untuk {image_path} ---")
        try:
            # 1. Pra-pemrosesan gambar (akan mengembalikan path file untuk YOLO)
            processed_input = self.ml_processor.preprocess_image(image_path)

            # 2. Prediksi menggunakan model Machine Learning (YOLOv8)
            ml_raw_results = self.ml_processor.predict_traffic(processed_input)

            # 3. Ekstraksi dan Klasifikasi Hasil
            extracted_data = self.ml_processor.extract_and_classify_results(ml_raw_results)
            print("Hasil Ekstraksi:")
            print(f"   Total Kendaraan: {extracted_data['total_num_vehicles']}")
            print(f"   Tingkat Lalu Lintas: {extracted_data['traffic_level']}")
            
            # Mendekode JSON untuk ditampilkan
            vehicle_counts = json.loads(extracted_data['vehicle_types_json'])
            print("   Jenis Kendaraan:")
            if not vehicle_counts:
                print("     Tidak ada kendaraan yang terdeteksi dari jenis yang ditentukan.")
            else:
                for v_type, count in vehicle_counts.items():
                    print(f"     - {v_type.capitalize()}: {count}")

            # 4. Menyimpan Hasil ke Database
            self.db_manager.save_analysis_result(
                image_filename=os.path.basename(image_path), # Simpan hanya nama file
                total_num_vehicles=extracted_data['total_num_vehicles'],
                traffic_level=extracted_data['traffic_level'],
                vehicle_types_json=extracted_data['vehicle_types_json'],
                raw_ml_output=extracted_data['raw_ml_output']
            )
            print(f"--- Analisis untuk {image_path} selesai ---")
            return True
        except FileNotFoundError as e:
            print(f"Error: File tidak ditemukan - {e}")
            return False
        except ValueError as e:
            print(f"Error dalam pemrosesan data atau gambar: {e}")
            return False
        except RuntimeError as e:
            print(f"Error dalam prediksi ML (pastikan model dan library terinstal dengan benar): {e}")
            return False
        except Exception as e:
            print(f"Terjadi kesalahan tidak terduga: {e}")
            import traceback
            traceback.print_exc() # Untuk melihat stack trace
            return False

# --- Bagian Utama untuk Menjalankan Aplikasi ---
if __name__ == "__main__":
    # Pastikan direktori untuk contoh gambar ada
    sample_images_dir = "storage_photo"
    if not os.path.exists(sample_images_dir):
        os.makedirs(sample_images_dir)
        print(f"Direktori '{sample_images_dir}' dibuat.")
        print("Pastikan untuk menempatkan gambar jalan raya asli di folder ini untuk pengujian.")
        # Buat file dummy agar script tidak crash, tetapi deteksi akan nol
        with open(os.path.join(sample_images_dir, "capture.jpg"), "w") as f:
            f.write("dummy content")

    # Inisialisasi aplikasi dengan YOLOv8x (model paling akurat)
    # Pastikan Anda telah mengunduh 'yolov8x.pt' dan menempatkannya di direktori kerja Anda.
    app = TrafficAnalysisApp(db_path='my_traffic_data_yolov8x.db', ml_model_name='yolov8x.pt') # <--- Diubah ke yolov8x.pt

    # Contoh penggunaan:
    # Ganti dengan path ke gambar asli Anda di folder sample_images
    target_image_name = "capture.jpg" # <--- Menggunakan capture.jpeg sesuai diskusi sebelumnya
    sample_image_path = os.path.join(sample_images_dir, target_image_name)

    found_real_image = False
    if os.path.exists(sample_image_path) and os.path.getsize(sample_image_path) > 1000:
        found_real_image = True
    
    if not found_real_image:
        print(f"\n[PERINGATAN] Gambar '{target_image_name}' tidak terdeteksi di '{sample_images_dir}' atau terlalu kecil.")
        print("Pastikan Anda telah menempatkan foto lalu lintas asli (misalnya, capture.jpeg) di folder tersebut.")
        # Jika gambar target tidak ditemukan, cari gambar lain yang valid di folder tersebut
        for fname in os.listdir(sample_images_dir):
            fpath = os.path.join(sample_images_dir, fname)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 1000 and fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                sample_image_path = fpath
                found_real_image = True
                print(f"Menggunakan gambar lain yang terdeteksi: {sample_image_path}")
                break
        
        if not found_real_image:
            print("Tidak ada gambar asli yang ditemukan di direktori. Keluar.")
            exit() # Keluar jika tidak ada gambar yang bisa dianalisis

    app.run_analysis(sample_image_path)

    print("\nSemua analisis selesai.")
    print(f"Data disimpan di database: {app.db_manager.db_path}")
    print("Anda dapat memeriksa file .db ini menggunakan DB Browser for SQLite.")