import sqlite3
import datetime

class DatabaseManager:
    def __init__(self, db_path='traffic_data.db'):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """
        Membuat tabel analisis lalu lintas jika belum ada.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    image_filename TEXT NOT NULL,
                    total_num_vehicles INTEGER NOT NULL,
                    traffic_level TEXT NOT NULL,
                    vehicle_types_json TEXT NOT NULL,
                    raw_ml_output TEXT NOT NULL
                )
            ''')
            conn.commit()
            print(f"Tabel 'traffic_analysis' siap di {self.db_path}.")
        except sqlite3.Error as e:
            print(f"Error saat membuat tabel database: {e}")
        finally:
            if conn:
                conn.close()

    def save_analysis_result(self, image_filename, total_num_vehicles, traffic_level, vehicle_types_json, raw_ml_output):
        """
        Menyimpan hasil analisis lalu lintas ke database.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO traffic_analysis (timestamp, image_filename, total_num_vehicles, traffic_level, vehicle_types_json, raw_ml_output)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, image_filename, total_num_vehicles, traffic_level, vehicle_types_json, raw_ml_output))
            conn.commit()
            print("Data analisis berhasil disimpan ke database.")
        except sqlite3.Error as e:
            print(f"Error saat menyimpan data ke database: {e}")
        finally:
            if conn:
                conn.close()

    def get_all_results(self):
        """
        Mengambil semua hasil analisis dari database.
        """
        conn = None
        results = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM traffic_analysis ORDER BY timestamp DESC')
            results = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error saat mengambil data dari database: {e}")
        finally:
            if conn:
                conn.close()
        return results