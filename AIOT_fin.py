import cv2
import mediapipe as mp
import paho.mqtt.client as mqtt
import time
import tkinter as tk
from tkinter import messagebox
import threading  # 為了讓彈出視窗不卡死主程式(選用)，這裡先用簡單版

# --- 設定區 ---

# 影像來源設定
URL = "http://10.168.203.98:8080/video" 

# MQTT 設定
BROKER_ADDRESS = "broker.hivemq.com"
PORT = 1883
TOPIC = "AIOT/Project/S12350312/Detected" # 設定Topic避免衝突
CLIENT_ID = "Camera_01"

# AI 偵測設定
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# --- MQTT 連線函式 ---
def connect_mqtt():
    client = mqtt.Client(CLIENT_ID)
    try:
        client.connect(BROKER_ADDRESS, PORT)
        print("已連線到 MQTT Broker")
        return client
    except Exception as e:
        print(f"MQTT 連線失敗: {e}")
        return None

# --- 電腦端彈出視窗函式 ---
def show_popup_alert():
    # 建立一個隱藏的主視窗
    root = tk.Tk()
    root.withdraw() # 隱藏主視窗，只顯示對話框
    # 設定視窗置頂
    root.attributes('-topmost', True)
    
    print("偵測到人物")
    messagebox.showwarning("偵測到人物")
    
    root.destroy() # 關閉視窗

# --- 主程式 ---
def main():
    client = connect_mqtt()
    
    print(f"嘗試連線到手機鏡頭: {URL} ...")
    cap = cv2.VideoCapture(URL)

    # 檢查是否成功開啟
    if not cap.isOpened():
        print("無法連線到手機鏡頭，確保手機和電腦連到相同的wifi")
        return

    last_detection_time = 0 
    detection_cooldown = 5 # 設定時間間隔，避免視窗一直跳出來

    print("按 'q' 結束")

    with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("讀取影像失敗 (網路可能中斷)")
                # 這裡可以試著加入重連機制，但為求簡單先 break
                break

            # 轉成 RGB
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_detection.process(image)

            # 轉回 BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # --- 核心邏輯 ---
            if results.detections:
                for detection in results.detections:
                    mp_drawing.draw_detection(image, detection)
                
                # 觸發條件
                current_time = time.time()
                if current_time - last_detection_time > detection_cooldown:
                    
                    # 發送 MQTT (手機接收通知)
                    if client:
                        msg = "偵測到人物"
                        client.publish(TOPIC, msg)
                        print(f"MQTT 訊息已發送: {msg}")

                    # 電腦跳出視窗
                    show_popup_alert()

                    last_detection_time = time.time()
            
            # 顯示畫面
            display_img = cv2.resize(image, (960, 540))
            cv2.imshow('Camera (Mobile Stream)', display_img)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()