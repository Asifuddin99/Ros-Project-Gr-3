import cv2, os, time

SAVE_DIR = os.path.join("data", "target")
os.makedirs(SAVE_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                     "haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    raise SystemExit("No camera found")

print("Position your face FRONTALLY in good light.")
print("Press SPACE to start auto-capture (20 images), or q to quit.")

count = 0
started = False
while True:
    ok, frame = cap.read()
    if not ok: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 3)

    # draw
    for (x,y,w,h) in faces:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    cv2.putText(frame, f"Saved: {count}/20", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.imshow("Capture target face", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    if key == 32:  # SPACE
        started = True

    # when started and exactly one face visible → save every 300 ms
    if started and len(faces) == 1:
        (x,y,w,h) = faces[0]
        roi = gray[y:y+h, x:x+w]
        roi = cv2.resize(roi, (200,200))
        filename = os.path.join(SAVE_DIR, f"img_{int(time.time()*1000)}.jpg")
        cv2.imwrite(filename, roi)
        count += 1
        time.sleep(0.3)
        if count >= 20:
            print("Done capturing 20 images.")
            break

cap.release()
cv2.destroyAllWindows()

print("Images saved in:", os.path.abspath(SAVE_DIR))
print("If count < 20, repeat to add more images.")

