import face_recognition
import datetime 
import pandas as pd

file_df = pd.read_csv('./data-File/data-list.csv')

# These lists will only store data for photos where a face was actually found
# if not valid photo, it will 
valid_encodings = []
valid_names = []
valid_ids = [] # Added this to track the IDs
valid_statuses = []

# uk = face_recognition.load_image_file('./unknown/jiaqi-7.jpeg', 'RGB')        # green face
uk = face_recognition.load_image_file('./red-list/mountain-02.webp', 'RGB')   # red face
# uk = face_recognition.load_image_file('./unknown/uk-00.webp', 'RGB')          # yellow face
uk_encodings = face_recognition.face_encodings(uk)

if len(uk_encodings) > 0:
    uk_encod = uk_encodings[0]

    for index, row in file_df.iterrows():
        path = row['File Name']
        img = face_recognition.load_image_file(path)
        encods = face_recognition.face_encodings(img)

        
        if len(encods) > 0:
            valid_encodings.append(encods[0])
            valid_names.append(row['Name'])
            valid_ids.append(row['ID'])   
            valid_statuses.append(row['Status'])

        else:
            print(f"\nNo face detected in: {path}\n")

    fnd_status = face_recognition.compare_faces(valid_encodings, uk_encod, tolerance=0.5)
    
    # test:
    # print(uk_encod)
    match_found = False

    for i, match in enumerate(fnd_status):
        if match:
            match_found = True
            matched_id = str(valid_ids[i])
            matched_name = valid_names[i]
            matched_status = valid_statuses[i]
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if matched_status == 'Denied':
                    print(f"\n🛑 RED ALERT! 🛑")
                    print(f"DENIED person detected: {matched_name}")
                    print(f"Time: {timestamp}")
                    print("Security notified.\n")
            else:
                print(f"Match found: {matched_name} (ID: {valid_ids[i]})")
                log_entry = f"{valid_ids[i]} {matched_name} {timestamp}\n"
                with open('./data-file/attendance.txt', "a") as log_file:
                    log_file.write(log_entry)    
            
            break # Stop looking once we find the first match

    if not match_found:
        print("Alert Code-Yellow: Face detected, but no match found in the database (Unknown Person).")

else:
    print("Could not find a face in the unknown image.\n")



