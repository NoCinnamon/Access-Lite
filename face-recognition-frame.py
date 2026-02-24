import face_recognition
import cv2
import os, sys
import numpy as np
import math

# calculate acuracy percentage of faces, and display it on the screen
def face_confidence(face_distance, match_threshold=0.6):
    range = (1.0-match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'
    

class FaceRecognition:
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_names = []
    process_currebt_frame = True    # so you dont have to recognize faces every single frame, insterad, do every other frame

    def __init__(self):
        self.encode_faces()

    def encode_faces(self):
        for image in os.listdir('Jiaqi'):
            if image.endswith(('.png', '.jpg', '.jpeg', 'JPG')):
                face_image = face_recognition.load_image_file(f'Jiaqi/{image}')
                encodings = face_recognition.face_encodings(face_image)
                # face_encoding = face_recognition.face_encodings(face_image)[0]
                
                if len(encodings) > 0:
                    self.face_encodings.append(encodings[0])
                    self.known_face_names.append(os.path.splitext(image)[0])
                    print(f"Successfully encoded: {image}")
            
                else:
                    print(f"No face detected in '{image}'. Skipping.")
            else:
                continue

        print(" ")
        print(self.known_face_names)
        print(" ")
        


if __name__ == '__main__':
    fr = FaceRecognition()