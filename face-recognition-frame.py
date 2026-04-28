import face_recognition
import cv2
import os, sys
import csv
import json
import math
import pickle
import platform
import subprocess
import threading
import urllib.error
import urllib.request
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

RED_LIST_ALERT_COOLDOWN_SEC = 15
# Looser than known_faces (0.6): live 1/4-scale frames often need a higher distance cutoff.
RED_LIST_MATCH_TOLERANCE = 0.72
# Training still uses 0.6; quarter-scale live video often scores slightly above that for real members.
KNOWN_FACE_MATCH_TOLERANCE = 0.60
# OpenCV uses BGR. Green = known; red = red_list match; yellow = stranger (no red/known match).
KNOWN_MATCH_BOX_BGR = (68, 250, 2)  #2f855a
RED_LIST_BOX_BGR = (0, 0, 255)
UNKNOWN_FACE_BOX_BGR = (0, 255, 255)
# Bundled alert (served under frontend/; Python plays it locally when red_list matches).
ALERT_SOUND_WAV = os.path.join(
    "frontend",
    "alert-soundEffect",
    "141244__tarrei__scream-sharks-take-1.wav",
)


# 1: calculate acuracy percentage of faces, and display it on the screen
def face_confidence(face_distance, match_threshold=0.6):
    range = (1.0 - match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > match_threshold:      # if not matching
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
        self._encoding_pickle_path = os.path.join(self._project_root, "encoding_database.pkl")
        self.red_list_encodings = []
        self.red_list_labels = []
        self._red_alert_cooldown = {}
        self._load_red_list_faces()

        if os.path.exists(self._encoding_pickle_path):
            print("loading database from Pickle file...")
            with open(self._encoding_pickle_path, "rb") as f:
                data = pickle.load(f)
                self.known_face_encodings = data["encodings"]
                self.known_face_names = data["names"]
        else:
            print("No Pickle file found.Encoding image from folder...")
            self.encode_faces()
            self.save_to_pickle()

        self._ensure_pickle_matches_known_faces()

        self.sync_members_from_csv_and_disk()
        self._load_face_to_member_id_map()

    def save_to_pickle(self):
        data = {
            'encodings': self.known_face_encodings,
            'names': self.known_face_names
        }

        with open(self._encoding_pickle_path, "wb") as f:
            pickle.dump(data, f)
        print(f"Database now saved to {self._encoding_pickle_path}")

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

    def _load_red_list_faces(self):
        """Encode faces in red_list/ — same extensions as known_faces. Not in pickle; reloaded each run."""
        rd = os.path.join(self._project_root, "red_list")
        if not os.path.isdir(rd):
            return
        for image in sorted(os.listdir(rd)):
            low = image.lower()
            if low == ".gitkeep" or not low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            path = os.path.join(rd, image)
            try:
                face_image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(face_image)
            except Exception as e:
                print(f"red_list: could not load '{image}': {e}")
                continue
            if len(encodings) == 0:
                print(f"red_list: no face in '{image}', skipping.")
                continue
            stem = os.path.splitext(image)[0]
            self.red_list_encodings.append(encodings[0])
            self.red_list_labels.append(stem)
            print(f"red_list: armed '{image}' ({stem})")
        if self.red_list_labels:
            print(f"red_list: {len(self.red_list_labels)} face(s) will trigger alert sound when matched.")
        print(
            f"red_list alert sound (from settings file): {'ON' if self._read_red_list_sound_enabled() else 'OFF'}",
            flush=True,
        )
        secret_set = bool(os.getenv("RED_LIST_ALERT_SECRET", "").strip())
        print(
            f"red_list admin email alerts: {'ON (set SMTP_* in .env on server)' if secret_set else 'OFF (set RED_LIST_ALERT_SECRET in .env)'}",
            flush=True,
        )

    def _read_red_list_sound_enabled(self):
        """Same flag as Node: data/camera_alert_settings.json → redListSoundEnabled (default on)."""
        p = os.path.join(self._project_root, "data", "camera_alert_settings.json")
        try:
            with open(p, encoding="utf-8") as f:
                j = json.load(f)
            return j.get("redListSoundEnabled", True) is not False
        except Exception:
            return True

    def _best_red_list_match_detail(self, face_encoding):
        """Best red_list candidate within tolerance, or (None, None)."""
        if not self.red_list_encodings:
            return None, None
        dists = face_recognition.face_distance(self.red_list_encodings, face_encoding)
        idx = int(np.argmin(dists))
        d = float(dists[idx])
        if d <= RED_LIST_MATCH_TOLERANCE:
            return self.red_list_labels[idx], d
        return None, None

    def _best_red_list_match(self, face_encoding):
        label, _ = self._best_red_list_match_detail(face_encoding)
        return label

    def _best_known_match_detail(self, face_encoding):
        """Closest known face if within KNOWN_FACE_MATCH_TOLERANCE, else (None, None)."""
        if not self.known_face_encodings:
            return None, None
        matche = face_recognition.compare_faces(
            self.known_face_encodings,
            face_encoding,
            tolerance=KNOWN_FACE_MATCH_TOLERANCE,
        )
        dists = face_recognition.face_distance(self.known_face_encodings, face_encoding)
        if len(dists) == 0:
            return None, None
        i = int(np.argmin(dists))
        if i < len(matche) and matche[i]:
            return self.known_face_names[i], float(dists[i])
        return None, None

    def _known_face_stems_on_disk(self):
        kf = os.path.join(self._project_root, "known_faces")
        stems = set()
        if not os.path.isdir(kf):
            return stems
        for f in os.listdir(kf):
            low = f.lower()
            if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                stems.add(os.path.splitext(f)[0])
        return stems

    def _ensure_pickle_matches_known_faces(self):
        """Stale encoding_database.pkl (missing new members like Saul-8) causes wrong nearest-neighbor hits."""
        disk = self._known_face_stems_on_disk()
        if not disk:
            return
        pickled = set(self.known_face_names)
        if disk == pickled:
            return
        print(
            f"encoding_database.pkl out of sync with known_faces/ "
            f"(folder {len(disk)} face(s), pickle {len(pickled)}). Re-encoding from disk...",
            flush=True,
        )
        self.known_face_encodings = []
        self.known_face_names = []
        self.encode_faces()
        self.save_to_pickle()

    def _alert_sound_wav_path(self):
        return os.path.join(self._project_root, ALERT_SOUND_WAV)

    def _play_alert_sound_async(self):
        path = self._alert_sound_wav_path()
        try:
            if not os.path.isfile(path):
                print(f"Alert sound file missing: {path}", flush=True)
                return
            system = platform.system()
            if system == "Darwin":
                afplay = "/usr/bin/afplay" if os.path.isfile("/usr/bin/afplay") else "afplay"
                print(f"Alert sound: playing via {afplay} → {path}", flush=True)
                subprocess.Popen(
                    [afplay, path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
            elif system == "Windows":
                import winsound

                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                subprocess.Popen(
                    ["aplay", "-q", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            print(f"Alert sound skipped: {e}", flush=True)

    def _notify_red_list_admins_async(self, red_label, when):
        if not os.getenv("RED_LIST_ALERT_SECRET", "").strip():
            return
        threading.Thread(
            target=self._post_red_list_alert_webhook,
            args=(red_label, when),
            daemon=True,
        ).start()

    def _post_red_list_alert_webhook(self, red_label, when):
        url = os.getenv(
            "RED_LIST_ALERT_URL",
            "http://127.0.0.1:8001/api/internal/red-list-alert",
        ).strip()
        secret = os.getenv("RED_LIST_ALERT_SECRET", "").strip()
        if not secret or not url:
            return
        body = json.dumps(
            {
                "redListLabel": red_label,
                "detectedAt": when.isoformat(timespec="seconds"),
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Alert-Secret": secret,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                if resp.status != 200:
                    print(f"red_list email notify HTTP {resp.status}: {raw}", flush=True)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            print(f"red_list email notify failed HTTP {e.code}: {err_body}", flush=True)
        except Exception as e:
            print(f"red_list email notify failed: {e}", flush=True)

    def _maybe_alert_red_list(self, red_label):
        if not red_label:
            return
        now = datetime.now()
        last = self._red_alert_cooldown.get(red_label)
        if last and (now - last).total_seconds() < RED_LIST_ALERT_COOLDOWN_SEC:
            return
        self._red_alert_cooldown[red_label] = now
        print(f"RED LIST ALERT: match '{red_label}'", flush=True)
        sound_on = self._read_red_list_sound_enabled()
        if not sound_on:
            print(
                "red_list alert sound: OFF (set redListSoundEnabled true in data/camera_alert_settings.json or dashboard)",
                flush=True,
            )
        else:
            self._play_alert_sound_async()
        self._notify_red_list_admins_async(red_label, now)

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
                self.face_box_bgr = []

                unknown_index = 0
                for unknown_face_encoding in self.face_encodings:
                    name = f'Unknown-{unknown_index}'
                    confidence = 'Unknown'
                    box_bgr = UNKNOWN_FACE_BOX_BGR
                    face_distances = face_recognition.face_distance(
                        self.known_face_encodings, unknown_face_encoding
                    )
                    if len(self.known_face_encodings) == 0:
                        face_distances = np.array([])

                    rl, dist_rl = self._best_red_list_match_detail(unknown_face_encoding)
                    kn, dist_kn = self._best_known_match_detail(unknown_face_encoding)
                    # If both gates pass, use the tighter embedding match so red_list test photos
                    # (e.g. yourself) do not override a registered member (e.g. Saul).
                    if (
                        rl is not None
                        and kn is not None
                        and dist_rl is not None
                        and dist_kn is not None
                    ):
                        if dist_kn < dist_rl:
                            rl, dist_rl = None, None
                        else:
                            kn, dist_kn = None, None

                    if rl is not None:
                        name = rl
                        confidence = face_confidence(dist_rl, RED_LIST_MATCH_TOLERANCE)
                        box_bgr = RED_LIST_BOX_BGR
                        if name not in self.current_attendees:
                            self.log_event(
                                name,
                                "Unauthorized",
                                datetime.now(),
                                identity_stem=name,
                            )
                        self.current_attendees[name] = datetime.now()
                        self._maybe_alert_red_list(rl)
                    elif kn is not None:
                        name = kn
                        confidence = face_confidence(dist_kn, KNOWN_FACE_MATCH_TOLERANCE)
                        box_bgr = KNOWN_MATCH_BOX_BGR
                        if name not in self.current_attendees:
                            self.log_event(name, "Arrived", datetime.now())
                        self.current_attendees[name] = datetime.now()
                    else:
                        if len(face_distances) > 0:
                            if name not in self.current_attendees:
                                self.log_event(
                                    name,
                                    "Unauthorized (Unknown)",
                                    datetime.now(),
                                )
                            self.current_attendees[name] = datetime.now()

                    self.face_names.append(f'{self.display_name_for_face(name)}({confidence})')
                    self.face_box_bgr.append(
                        box_bgr if len(face_distances) > 0 else UNKNOWN_FACE_BOX_BGR
                    )
                    unknown_index += 1
                self.get_left_time()
            self.process_current_frame = not self.process_current_frame

            for (top, right, bottom, left), name, bgr in zip(
                self.face_locations, self.face_names, self.face_box_bgr
            ):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), bgr, 3)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), bgr, 3)
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

    def log_event(self, name, status, timestamp, *, identity_stem=None):
        """identity_stem: for red_list Unauthorized, use the red_list filename stem so Name/ID are not remapped to UNKNOWN."""
        face_stem = name
        if identity_stem is not None and str(identity_stem).strip():
            key = str(identity_stem).strip()
        else:
            key = self._canonical_face_key_for_detection(face_stem)
        display_name = self.display_name_for_face(key)
        student_id = self.resolve_student_id(key)
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
            f"ENTRY RECORDED: {key} marked as {status} at {time_string}",
            flush=True,
        )
        # Node (ingestStdoutForDetections) matches members by faceKey / memberID / pickle stem.
        if status == "Arrived":
            raw_stem = str(face_stem or "").strip()
            sid = str(student_id or "").strip()
            detect_parts = []
            for part in (str(key or "").strip(), sid, raw_stem):
                if part and part not in detect_parts:
                    detect_parts.append(part)
            if detect_parts:
                print(f"SESSION_DETECT_KEYS: {'|'.join(detect_parts)}", flush=True)

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
