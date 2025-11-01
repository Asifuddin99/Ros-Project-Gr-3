import cv2, os, glob, numpy as np, serial, time

# ==== EDIT THIS ====
SERIAL_PORT = "COM5"   # <-- change to your Pico port (COM3/COM4/COM5 etc.)
BAUD = 115200
OPEN_CMD = b"OPEN\n"
DETECTION_COOLDOWN = 5.0
# ====================

print("Working dir:", os.getcwd())

# 1) load training images from data/target/
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                     "haarcascade_frontalface_default.xml")
imgs, labels = [], []
for p in glob.glob(os.path.join("data","target","*.*")):
    img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    if img is None: 
        continue
    # if images are raw crops from capture_faces, they’re already 200x200
    # still, detect once more for robustness
    faces = face_cascade.detectMultiScale(img, 1.1, 3)
    if len(faces) == 0:
        # assume it’s already a face crop
        face_roi = cv2.resize(img, (200,200))
        imgs.append(face_roi); labels.append(1)
    else:
        for (x,y,w,h) in faces:
            roi = cv2.resize(img[y:y+h, x:x+w], (200,200))
            imgs.append(roi); labels.append(1)

print(f"Found {len(imgs)} training face(s).")
if not imgs:
    raise SystemExit("No training faces found in data/target/. Run capture_faces.py first.")

# 2) train LBPH
recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
recognizer.train(imgs, np.array(labels))

# 3) serial + camera
try:
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1); time.sleep(1)
    print("Serial opened:", SERIAL_PORT)
except Exception as e:
    print("Serial error:", e)
    ser = None

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    raise SystemExit("Camera not available")

last_open = 0
print("Running… press q to quit.")
while True:
    ok, frame = cap.read()
    if not ok: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.1, 3)
    match = False
    conf_display = 9999.0

    for (x,y,w,h) in faces:
        roi = cv2.resize(gray[y:y+h, x:x+w], (200,200))
        label, conf = recognizer.predict(roi)  # lower conf = better
        conf_display = conf
        if label == 1 and conf < 65:  # tune 40–75
            match = True
            color = (0,255,0)
        else:
            color = (0,0,255)
        cv2.rectangle(frame, (x,y), (x+w, y+h), color, 2)

    cv2.putText(frame, f"Match:{match} conf:{conf_display:.1f}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.imshow("Recognize target", frame)

    now = time.time()
    if match and (now - last_open) > DETECTION_COOLDOWN and ser:
        ser.write(OPEN_CMD); print("Sent OPEN")
        last_open = now

    if (cv2.waitKey(1) & 0xFF) == ord('q'):
        break

cap.release(); cv2.destroyAllWindows()
if ser: ser.close()
