import face_recognition
import cv2
import os, sys
import csv
import numpy as np
import math
import pickle
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient


# 1: calculate acuracy percentage of faces, and display it on the screen
def face_confidence(face_distance, match_threshold=0.6):
    range = (1.0 - match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'


class FaceRecognition:
    # Photos in known_faces: "DisplayName-MemberID.jpg". Registry: data/members.csv + MongoDB "members".
    # Legacy files with no hyphen: whole stem is both name and ID.

    @staticmethod
    def parse_face_identity(stem: str):
        s = (stem or "").strip()
        if not s or s.lower().startswith("unknown"):
            return "Unknown", "UNKNOWN"
        parts = s.rsplit("-", 1)
        if len(parts) == 2 and parts[1].strip():
            return parts[0].strip(), parts[1].strip()
        return s, s

    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []

        self.current_attendees = {}  # face stem -> last_seen

        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_current_frame = True

        env_path = "/Users/jiaqi/git-project/Access-Lite/.env"
        load_dotenv(dotenv_path=env_path)
        mongo_uri = os.getenv("MONGO_URI")
        print(f"DEBUG: URI found? {mongo_uri is not None}")
        self.client = MongoClient(mongo_uri)
        self.db = self.client["attendence"]
        self.collection = self.db["Attendance-Logs"]
        self._face_to_member_id = {}
        self._project_root = os.path.dirname(os.path.abspath(__file__))

        if os.path.exists("encoding_database.pkl"):
            print("loading database from Pickle file...")
            with open("encoding_database.pkl", "rb") as f:
                data = pickle.load(f)
                self.known_face_encodings = data["encodings"]
                self.known_face_names = data["names"]
        else:
            print("No Pickle file found.Encoding image from folder...")
            self.encode_faces()
            self.save_to_pickle()

        self.sync_members_from_csv_and_disk()
        self._load_face_to_member_id_map()

    def save_to_pickle(self):
        data = {
            'encodings': self.known_face_encodings,
            'names': self.known_face_names
        }

        with open('encoding_database.pkl', 'wb') as f:
            pickle.dump(data, f)
        print("Database now saved to encoding_database.pkl")

    def encode_faces(self):
        kf = os.path.join(self._project_root, "known_faces")
        for image in os.listdir(kf):
            if image.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                face_image = face_recognition.load_image_file(os.path.join(kf, image))
                encodings = face_recognition.face_encodings(face_image)

                if len(encodings) > 0:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(os.path.splitext(image)[0])
                    print(f"Successfully encoded: {image}")

                else:
                    print(f"No face detected in '{image}'. Skipping.")
            else:
                continue

        print(" ")
        print(self.known_face_names)
        print(" ")

    def _members_csv_path(self):
        return os.path.join(self._project_root, "data", "members.csv")

    def sync_members_from_csv_and_disk(self):
        """Merge known_faces filenames with data/members.csv → MongoDB `members` (same rules as Node)."""
        kf = os.path.join(self._project_root, "known_faces")
        csv_path = self._members_csv_path()
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        csv_by_key = {}
        if os.path.isfile(csv_path) and os.path.getsize(csv_path) > 0:
            try:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    r = csv.DictReader(f)
                    for row in r:
                        fk = (row.get("faceKey") or "").strip()
                        if fk:
                            csv_by_key[fk] = row
            except Exception as e:
                print(f"Warning reading members.csv: {e}")
        merged = []
        if os.path.isdir(kf):
            for image in os.listdir(kf):
                if not image.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    continue
                stem = os.path.splitext(image)[0]
                display_name, mid = self.parse_face_identity(stem)
                photo_path = f"known_faces/{image}"
                extra = csv_by_key.get(stem, {})
                merged.append(
                    {
                        "faceKey": stem,
                        "name": display_name,
                        "memberID": mid,
                        "photoPath": photo_path,
                        "contact": (extra.get("contact") or "").strip(),
                        "notes": (extra.get("notes") or "").strip(),
                    }
                )
        merged.sort(key=lambda x: x["faceKey"])
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=["faceKey", "name", "memberID", "photoPath", "contact", "notes"],
                )
                w.writeheader()
                for m in merged:
                    w.writerow(m)
        except Exception as e:
            print(f"Could not write members.csv: {e}")
        keys = [m["faceKey"] for m in merged]
        try:
            col = self.db["members"]
            if not keys:
                col.delete_many({})
            else:
                col.delete_many({"faceKey": {"$nin": keys}})
            now = datetime.now()
            for m in merged:
                col.update_one(
                    {"faceKey": m["faceKey"]},
                    {
                        "$set": {**m, "updatedAt": now},
                        "$setOnInsert": {"createdAt": now},
                    },
                    upsert=True,
                )
            print(f'Members synced: {len(merged)} row(s) → "members" + data/members.csv')
        except Exception as e:
            print(f"Members Mongo sync skipped: {e}")

    def _load_face_to_member_id_map(self):
        self._face_to_member_id = {}
        try:
            for doc in self.db["members"].find({}):
                mid = doc.get("memberID")
                if mid is None or str(mid).strip() == "":
                    continue
                fk = doc.get("faceKey")
                if fk and str(fk).strip():
                    self._face_to_member_id[str(fk).strip()] = str(mid).strip()
        except Exception as e:
            print(f"Note: could not load members -> memberID map: {e}")

    def resolve_student_id(self, face_stem: str) -> str:
        """Attendance log ID: memberID from `members`, else parsed from filename stem."""
        fn = (face_stem or "").strip()
        if not fn or fn.lower().startswith("unknown"):
            return "UNKNOWN"
        roster = self._face_to_member_id.get(fn)
        if roster:
            return roster
        _, parsed_id = self.parse_face_identity(fn)
        return parsed_id

    def _canonical_face_key_for_detection(self, pickled_name: str) -> str:
        """Align pickle label with current known_faces / Mongo faceKey (Node session marks match this)."""
        raw = (pickled_name or "").strip()
        if not raw or raw.lower().startswith("unknown"):
            return raw
        roster = getattr(self, "_face_to_member_id", None) or {}
        if raw in roster:
            return raw
        kf = os.path.join(self._project_root, "known_faces")
        disk_stems = set()
        if os.path.isdir(kf):
            for f in os.listdir(kf):
                low = f.lower()
                if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                    disk_stems.add(os.path.splitext(f)[0])
        if raw in disk_stems:
            return raw
        display_pick = self.parse_face_identity(raw)[0].lower()
        if not display_pick:
            return raw
        matches = []
        try:
            for doc in self.db["members"].find({}):
                fk = (doc.get("faceKey") or "").strip()
                if not fk:
                    continue
                disp = self.parse_face_identity(fk)[0].lower()
                if disp == display_pick:
                    matches.append(fk)
        except Exception:
            pass
        uniq = sorted(set(matches))
        if len(uniq) == 1:
            return uniq[0]
        return raw

    def display_name_for_face(self, face_stem: str) -> str:
        return self.parse_face_identity(face_stem)[0]

    def run_recognition(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            print("Video source not found.")

        while True:
            ret, frame = video_capture.read()

            if self.process_current_frame:
                size_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_size_frame = cv2.cvtColor(size_frame, cv2.COLOR_BGR2RGB)

                self.face_locations = face_recognition.face_locations(rgb_size_frame)
                self.face_encodings = face_recognition.face_encodings(rgb_size_frame, self.face_locations)
                self.face_names = []

                unknown_index = 0
                for unknown_face_encoding in self.face_encodings:
                    matche = face_recognition.compare_faces(self.known_face_encodings, unknown_face_encoding)
                    name = f'Unknown-{unknown_index}'
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

                        self.current_attendees[name] = datetime.now()

                    self.face_names.append(f'{self.display_name_for_face(name)}({confidence})')
                    unknown_index += 1
                self.get_left_time()
            self.process_current_frame = not self.process_current_frame

            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 3)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), 3)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow('Face Recognition', frame)

            if cv2.waitKey(1) == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def get_start_time(self):
        start_time = datetime.now()
        return start_time

    def get_left_time(self):
        now = datetime.now()
        for name_in_room, last_seen in list(self.current_attendees.items()):
            seconds_missing = (now - last_seen).total_seconds()

            if seconds_missing > 5:
                self.log_event(name_in_room, "Left", last_seen)
                del self.current_attendees[name_in_room]

    def log_event(self, name, status, timestamp):
        face_stem = name
        canonical = self._canonical_face_key_for_detection(face_stem)
        display_name = self.display_name_for_face(canonical)
        student_id = self.resolve_student_id(canonical)
        time_string = timestamp.strftime('%H:%M:%S')
        date_filename = timestamp.strftime('./CSVs/attendence_%Y-%m-%d.csv')
        date_str = timestamp.strftime('%Y-%m-%d')

        file_exists = os.path.isfile(date_filename)
        header_line = None
        if file_exists:
            with open(date_filename, 'r', encoding='utf-8') as rf:
                header_line = rf.readline().strip()

        with open(date_filename, 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write('StudentID,Name,Status,Time')
                f.write(f'\n{student_id},{display_name},{status},{time_string}')
            elif header_line and header_line.startswith('StudentID'):
                f.write(f'\n{student_id},{display_name},{status},{time_string}')
            else:
                f.write(f'\n{display_name},{status},{time_string}')

        print(
            f"ENTRY RECORDED: {canonical} marked as {status} at {time_string}",
            flush=True,
        )

        if self.collection is not None:
            document = {
                "studentID": student_id,
                "name": display_name,
                "status": status,
                "time": time_string,
                "date": date_str,
            }
            try:
                print(f"Attempting to push {display_name} ({student_id}) to MongoDB Atlas...")
                if self.collection.count_documents(document) == 0:
                    self.collection.insert_one(document)
                    print(f"DATABASE UPDATED: {display_name} is now in the cloud!")
                else:
                    print(f"Note: {display_name} already exists in DB for this exact time.")
            except Exception as e:
                print(f"DB ERROR: {e}")
        else:
            print("DB ERROR: self.collection is None. Check your __init__ connection.")

if __name__ == '__main__':
    fr = FaceRecognition()
    fr.run_recognition()
