import face_recognition
import cv2
import os, sys
import numpy as np
import math

# 1: calculate acuracy percentage of faces, and display it on the screen
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
    known_face_encodings = []
    face_names = []
    known_face_names = []
    process_currebt_frame = True    # so you dont have to recognize faces every single frame, insterad, do every other frame

    def __init__(self):
        self.encode_faces()

    def encode_faces(self):
        for image in os.listdir('JPhonex'):
            if image.endswith(('.png', '.jpg', '.jpeg', 'JPG')):
                face_image = face_recognition.load_image_file(f'JPhonex/{image}')
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
        print(self.known_face_names)    # now the images in folder 'Jiaqi' are initialized
        print(" ")
        


# 2: 
    def run_recognition(self):
        video_capture = cv2.VideoCapture(0)     # 你就一个camera， 0 是 index of camera
        if not video_capture.isOpened():
            print("Video source not found.")

        while True:
            ret, frame = video_capture.read() # weeither the fram is success or not, if there is no frame to process, ret will turn False!
            
            if self.process_currebt_frame:
                size_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
                # rgb_size_frame = np.ascontiguousarray(size_frame[:, :, ::-1])     # Color Flip (Swaps BGR to RGB )
                rgb_size_frame = cv2.cvtColor(size_frame, cv2.COLOR_BGR2RGB)        # new way of flip
# locate all faces in the current frame:
                self.face_locations = face_recognition.face_locations(rgb_size_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_size_frame, self.face_locations)
                self.face_names = []
                for face_encoding in self.face_encodings:
                    matche = face_recognition.compare_faces(self.face_encodings, face_encoding)
                    name = 'Unknown'                # 如果没找到 match 的face， 就会显示unknown， 但是， 它 没 有！！！！！！！！！！！
                    confidence = 'Unknown'

                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances) # Finds the smallest distance

                        if matche[best_match_index]:
                            name = self.known_face_names[best_match_index]
                            confidence = face_confidence(face_distances[best_match_index])
                    self.face_names.append(f'{name}({confidence})') 

            self.process_currebt_frame = not self.process_currebt_frame

            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *=4
                right *= 4
                bottom *= 4
                left *=4

                cv2.rectangle(frame, (left, top), (right,bottom), (0, 0, 255))
                cv2.rectangle(frame, (left, bottom-35), (right,bottom), (0, 0, 255))
                cv2.putText(frame, name, (left+6, bottom-6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
            

            cv2.imshow('Face Recognition', frame)

            if cv2.waitKey(1) == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()




if __name__ == '__main__':
    fr = FaceRecognition()
    fr.run_recognition()  # <--- You must call this to open the window!