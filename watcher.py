import time
import os
import sys
import subprocess
# --- Perubahan di sini: Menggunakan PollingObserver ---
from watchdog.observers.polling import PollingObserver 
from watchdog.events import FileSystemEventHandler

# --- Konfigurasi ---
# Pastikan path ini benar-benar absolut dan sesuai dengan lokasi file Anda di drive Windows
# yang diakses dari WSL (misalnya /mnt/d/...)
WATCH_DIRECTORY = "/mnt/d/ai/ai-vehicle-classification/storage_photo" # <-- Folder yang akan diawasi
MAIN_APP_SCRIPT = "app.py"    # Script yang akan dijalankan saat ada perubahan
PYTHON_EXECUTABLE = "python3" # <-- DIUBAH SECARA SPESIFIK KE "python3"

# --- DEBUG: Cetak jalur absolut saat startup ---
print(f"DEBUG: PATH ABSOLUT DIREKTORI DIAMATI: {os.path.abspath(WATCH_DIRECTORY)}")
print(f"DEBUG: PYTHON EXECUTABLE: {PYTHON_EXECUTABLE}")
print(f"DEBUG: SCRIPT APP UTAMA: {MAIN_APP_SCRIPT}")
# --- Akhir DEBUG ---

class MyHandler(FileSystemEventHandler):
    def __init__(self, watch_dir, app_script, python_exe):
        self.watch_dir = watch_dir
        self.app_script = app_script
        self.python_exe = python_exe
        # Dictionary untuk menyimpan timestamp modifikasi terakhir dari SETIAP file yang diproses
        self.processed_files_mtimes = {} 
        print(f"Watchdog: Mengawasi direktori: {self.watch_dir}")
        print(f"Watchdog: Akan menjalankan '{self.python_exe} {self.app_script}' untuk setiap file gambar baru/termodifikasi.")

    def _process_file(self, file_path):
        """
        Fungsi helper untuk memproses file, hanya jika itu adalah file gambar.
        """
        # Filter untuk memastikan hanya file gambar yang diproses
        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            print(f"DEBUG: Melewatkan file non-gambar: {file_path}")
            return

        # Pastikan file ada sebelum mencoba mendapatkan mtime (ini penting jika file dihapus terlalu cepat)
        if not os.path.exists(file_path):
            print(f"Watchdog: File {file_path} tidak ditemukan saat event. Melewatkan.")
            return

        current_mtime = os.path.getmtime(file_path)

        # Cek apakah file sudah diproses baru-baru ini berdasarkan timestamp
        if file_path in self.processed_files_mtimes and self.processed_files_mtimes[file_path] == current_mtime:
            print(f"DEBUG: Melewatkan {file_path} karena sudah diproses baru-baru ini (mtime sama).")
            return

        print(f"\n--- Watchdog mendeteksi perubahan pada file: {file_path} ---")
        
        # Tambahkan sedikit jeda untuk memastikan file selesai ditulis/disimpan
        time.sleep(1) 

        try:
            # Jalankan app.py sebagai subprocess dengan path file sebagai argumen
            command = [self.python_exe, self.app_script, file_path]
            
            # --- DEBUG: Cetak perintah yang akan dieksekusi ---
            print(f"DEBUG: Perintah yang akan dieksekusi: {' '.join(command)}")
            print(f"DEBUG: Memulai subprocess...")
            # --- Akhir DEBUG ---

            process = subprocess.run(command, capture_output=True, text=True, check=True)
            
            # --- DEBUG: Output dari app.py ---
            print("--- Output dari app.py ---")
            print(process.stdout)
            if process.stderr:
                print("--- Error dari app.py ---")
                print(process.stderr)
            print("--- app.py selesai ---")
            # --- Akhir DEBUG ---

            # Setelah berhasil diproses, catat timestamp modifikasi terakhir
            self.processed_files_mtimes[file_path] = current_mtime

        except subprocess.CalledProcessError as e:
            print(f"Watchdog Error: '{self.app_script}' gagal dengan exit code {e.returncode}")
            print(f"Watchdog Error Output: {e.stderr}")
        except FileNotFoundError:
            print(f"Watchdog Error: Interpreter '{self.python_exe}' atau script '{self.app_script}' tidak ditemukan di path yang ditentukan.")
            print(f"Pastikan '{self.python_exe}' adalah path yang valid ke interpreter Python Anda, dan '{self.app_script}' ada di direktori yang sama atau di PATH.")
        except Exception as e:
            print(f"Watchdog Error: Terjadi kesalahan tidak terduga saat menjalankan '{self.app_script}': {e}")
            import traceback
            traceback.print_exc() # Cetak stack trace lengkap untuk debug lebih lanjut

    def on_created(self, event):
        """Dipanggil ketika sebuah file atau direktori dibuat."""
        if not event.is_directory:
            print(f"DEBUG: Event on_created terpicu untuk: {event.src_path}") # Debug print
            self._process_file(event.src_path)

    def on_modified(self, event):
        """Dipanggil ketika sebuah file atau direktori dimodifikasi."""
        if not event.is_directory:
            print(f"DEBUG: Event on_modified terpicu untuk: {event.src_path}") # Debug print
            self._process_file(event.src_path)
    

if __name__ == "__main__":
    # Pastikan direktori WATCH_DIRECTORY ada
    if not os.path.exists(WATCH_DIRECTORY):
        os.makedirs(WATCH_DIRECTORY)
        print(f"Direktori '{WATCH_DIRECTORY}' dibuat.")
        
    event_handler = MyHandler(WATCH_DIRECTORY, MAIN_APP_SCRIPT, PYTHON_EXECUTABLE)
    # --- Perubahan di sini: Menggunakan PollingObserver ---
    observer = PollingObserver() 
    # recursive=False untuk hanya mengawasi folder utama, bukan subfolder di dalamnya
    # Jika Anda ingin mengawasi subfolder, ubah ini menjadi recursive=True
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False) 
    observer.start()
    try:
        while True:
            time.sleep(1) # Interval polling default untuk PollingObserver adalah 1 detik
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Watchdog berhenti.")