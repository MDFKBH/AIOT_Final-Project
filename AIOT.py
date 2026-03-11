import cv2
import mediapipe as mp
import paho.mqtt.client as mqtt
import time

# --- 設定區 ---
# 1. MQTT 設定
BROKER_ADDRESS = "broker.hivemq.com" # 使用公開的免費 Broker
PORT = 1883
TOPIC = "School/MyID/Alert" # ★重要：請把 MyID 改成你的學號，避免跟別人撞台
CLIENT_ID = "SecurityCam_01"

# 2. AI 偵測設定 (使用 MediaPipe)
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# --- MQTT 連線函式 ---
def connect_mqtt():
    client = mqtt.Client(CLIENT_ID)
    try:
        client.connect(BROKER_ADDRESS, PORT)
        print("已連線到 MQTT Broker!")
        return client
    except Exception as e:
        print(f"連線失敗: {e}")
        return None

# --- 主程式 ---
def main():
    client = connect_mqtt()
    cap = cv2.VideoCapture(0) # 開啟預設鏡頭
    
    last_alert_time = 0 # 用來控制警報頻率，不要一直狂發

    with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                continue

            # 轉成 RGB 給 AI 辨識
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_detection.process(image)

            # 轉回 BGR 給視窗顯示
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # --- 核心邏輯：如果有偵測到人臉 ---
            if results.detections:
                for detection in results.detections:
                    # 畫出框框 (讓 Demo 畫面看起來比較厲害)
                    mp_drawing.draw_detection(image, detection)
                
                # 發送 MQTT 警報 (限制每 5 秒發一次，避免洗版)
                if time.time() - last_alert_time > 5:
                    if client:
                        msg = "警告：偵測到不明人士！"
                        client.publish(TOPIC, msg)
                        print(f"以發送警報: {msg}")
                        last_alert_time = time.time()
            
            # 顯示畫面
            cv2.imshow('AI Security Camera', image)
            
            # 按 'q' 離開
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()