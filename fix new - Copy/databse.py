from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from datetime import datetime
import requests 

class Database:
    def __init__(self):
        self.MONGO_URI = "mongodb+srv://meraXi:1234@sicbatch6.1o8uifx.mongodb.net/?retryWrites=true&w=majority"
        self.UBIDOTS_TOKEN = "BBUS-5mJfbNMiM5BrRSQOWiIO4H0qLH0qJi"
        self.client = self._get_client()
    
    def _get_client(self):
        client = MongoClient(self.MONGO_URI, server_api=ServerApi('1'))
        try:
            client.admin.command('ping')
            return client
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return None
    
    def save_interaction(self, data):
        if not self.client:
            return False
        
        try:
            db = self.client['SPIDER-SENSE']
            db['Interaksi'].insert_one(data)
            return True
        except Exception as e:
            print(f"Error saving interaction: {e}")
            return False
    
    def update_background_data(self):
        if not self.client:
            return
        
        days_map = {
            "Monday": "senin", "Tuesday": "selasa", "Wednesday": "rabu",
            "Thursday": "kamis", "Friday": "jumat", "Saturday": "sabtu", "Sunday": "minggu"
        }
        
        now = datetime.now()
        day = days_map.get(now.strftime("%A"), "unknown")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            db = self.client['SPIDER-SENSE']
            
            # Simpan data penggunaan alat
            db['PenggunaanAlat'].insert_one({
                "hari": day,
                "timestamp": timestamp,
                "komponen": "Alat Aktif",
                "jumlah": 1
            })
            
            # Simpan data emosi dummy
            db['DataEmosi'].insert_one({
                "Ekspresi": "netral",
                "Jumlah": 1,
                "hari": day,
                "timestamp": timestamp
            })
            
            # Kirim ke Ubidots
            self._send_ubidots(day)
            
        except Exception as e:
            print(f"Error updating background data: {e}")
    
    def _send_ubidots(self, day):
        url = "http://industrial.api.ubidots.com/api/v1.6/devices/spider-sense/"
        headers = {"X-Auth-Token": self.UBIDOTS_TOKEN, "Content-Type": "application/json"}
        
        try:
            payload = {
                day: {"value": 1},
                "jumlah_emosi": {"value": 1},
                "netral": {"value": 1}
            }
            requests.post(url, headers=headers, json=payload, timeout=10)
        except Exception as e:
            print(f"Error sending to Ubidots: {e}")