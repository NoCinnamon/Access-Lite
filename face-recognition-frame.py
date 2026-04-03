import face_recognition
import cv2
import os, sys
import numpy as np
import math
import pickle
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient





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
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []

        self.current_attendees = {}             # Stores {name: last_seen_datetime}

        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_current_frame = True       # so you dont have to recognize faces every single frame, insterad, do every other frame
        self.encode_faces()


        env_path = "/Users/jiaqi/git-project/Access-Lite/.env" 
        load_dotenv(dotenv_path=env_path)
        mongo_uri = os.getenv("MONGO_URI")
        print(f"DEBUG: URI found? {mongo_uri is not None}") # This will tell us if it's loading
        self.client = MongoClient(mongo_uri)
        self.db = self.client['attendence']
        self.collection = self.db['Attendance-Logs']


# pickleing:
        if os.path.exists('encoding_database.pkl'):
            print("loading database from Pickle file...")
            with open('encoding_database.pkl', 'rb') as f:
                data = pickle.load(f)
                self.known_face_encodings = data['encodings']
                self.known_face_names = data['names']
        else:
            print("No Pickle file found.Encoding image from folder...")
            self.encode_faces()
            self.save_to_pickle()

    def save_to_pickle(self):
        data= {
            'encodings': self.known_face_encodings,
            'names': self.known_face_names
        }

        with open('encoding_database.pkl', 'wb') as f:
            pickle.dump(data, f)
        print("Database now saved to encoding_database.pkl")


    def encode_faces(self):
        for image in os.listdir('known_faces'):
            if image.endswith(('.png', '.jpg', '.jpeg', 'JPG')):
                face_image = face_recognition.load_image_file(f'known_faces/{image}')
                encodings = face_recognition.face_encodings(face_image)
                # face_encoding = face_recognition.face_encodings(face_image)[0]
                
                if len(encodings) > 0:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(os.path.splitext(image)[0])
                    print(f"Successfully encoded: {image}")
            
                else:
                    print(f"No face detected in '{image}'. Skipping.")
            else:
                continue

        print(" ")
        print(self.known_face_names)            # now the images in folder 'Jiaqi' are initialized
        print(" ")
        
# 2: 
    def run_recognition(self):
        video_capture = cv2.VideoCapture(0)     # 你就一个camera， 0 是 index of camera
        if not video_capture.isOpened():
            print("Video source not found.")

        while True:
            ret, frame = video_capture.read()   # weeither the fram is success or not, if there is no frame to process, ret will turn False!
            
            if self.process_current_frame:
                size_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
                # rgb_size_frame = np.ascontiguousarray(size_frame[:, :, ::-1])     # Color Flip (Swaps BGR to RGB )
                rgb_size_frame = cv2.cvtColor(size_frame, cv2.COLOR_BGR2RGB)        # new way of flip
                
                # locate all faces in the current frame:
                self.face_locations = face_recognition.face_locations(rgb_size_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_size_frame, self.face_locations)
                self.face_names = []

                unknown_index = 0
                for unknown_face_encoding in self.face_encodings:
                    matche = face_recognition.compare_faces(self.known_face_encodings, unknown_face_encoding)
                    name = f'Unknown-{unknown_index}'                # 如果没找到 match 的face， 就会显示unknown， 但是， 它 没 有！！！！！！！！！！！ 现在有了。
                    confidence = 'Unknown'
                    face_distances = face_recognition.face_distance(self.known_face_encodings, unknown_face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)

                        if len(matche) > 0 and matche[best_match_index]:
                            name = self.known_face_names[best_match_index]
                            confidence = face_confidence(face_distances[best_match_index])
                            
                            if name not in self.current_attendees:
                                self.log_event(name, "Arrived", datetime.now())
                        else:
                            if name not in self.current_attendees:
                                self.log_event(name, 'Unauthorized', datetime.now())

                            # # Always update 'Last Seen' so the 30s timer resets
                            # self.current_attendees[name] = datetime.now()

                        self.current_attendees[name] = datetime.now()
                                         
                    self.face_names.append(f'{name}({confidence})') 
                    unknown_index += 1
                self.get_left_time()
            self.process_current_frame = not self.process_current_frame
#             Frame 1: True → Run the heavy AI math (Find faces, compare encodings).
#             Frame 2: False → Skip the math. Just show the video.
#             Frame 3: True → Run the AI math again.

            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *=4             # Earlier in your run_recognition function, resized the frame to 1/4 size (fx=0.25, fy=0.25) to help the AI process the image faster.
                right *= 4          # Now the AI found the face on a small image, the coordinates are small. 
                bottom *= 4         # so to draw the box on the original large video frame, you must multiply those coordinates by 4 to scale them back up.
                left *=4

                cv2.rectangle(frame, (left, top), (right,bottom), (0, 0, 255), 3)
                cv2.rectangle(frame, (left, bottom-35), (right,bottom), (0, 0, 255), 3)
                cv2.putText(frame, name, (left+6, bottom-6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
            

            cv2.imshow('Face Recognition', frame)

            if cv2.waitKey(1) == ord('q'):      # If you pressed 'q', the break command stops the 'while True' loop immediately.
                break                           # 按 ‘q’ 就退出了, change ‘ord('q')’ to 27(ASCII for esc) 也行。 感觉好像有点神秘又 fancy 的样纸。

        video_capture.release()
        cv2.destroyAllWindows()


    def get_start_time(self):
        start_time = datetime.now()
        return start_time
    
   
    def get_left_time(self):
        now = datetime.now()
        # We use list() so we can delete items while looping
        for name_in_room, last_seen in list(self.current_attendees.items()):
            seconds_missing = (now - last_seen).total_seconds()
            
            if seconds_missing > 5: 
                # The time they actually left was their 'last_seen' time
                self.log_event(name_in_room, "Left", last_seen)
                
                # Remove them so they can 'Arrive' again later
                del self.current_attendees[name_in_room]
                

    def log_event(self, name, status, timestamp):
        time_string = timestamp.strftime('%H:%M:%S')
        date_filename = timestamp.strftime('./CSVs/attendence_%Y-%m-%d.csv')
        
        file_exists = os.path.isfile(date_filename)
        
        with open(date_filename, 'a') as f:
            if not file_exists:
                f.write('Name,Status,Time')
            f.write(f'\n{name},{status},{time_string}')

            
        print(f"ENTRY RECORDED: {name} marked as {status} at {time_string}")


        if self.collection is not None:
            document = {
                "name": name,
                "status": status,
                "time": time_string,
                "date": timestamp.strftime('%Y-%m-%d')
            }
            try:
                print(f"Attempting to push {name} to MongoDB Atlas...")
                # Check for duplicates
                if self.collection.count_documents(document) == 0:
                    self.collection.insert_one(document)
                    print(f"DATABASE UPDATED: {name} is now in the cloud!")
                else:
                    print(f"Note: {name} already exists in DB for this exact time.")
            except Exception as e:
                print(f"DB ERROR: {e}")
        else:
            print("DB ERROR: self.collection is None. Check your __init__ connection.")

if __name__ == '__main__':
    fr = FaceRecognition()
    fr.run_recognition()  # <--- You must call this to open the window!  da!