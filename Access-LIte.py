import face_recognition
import cv2
from PIL import ImageDraw, ImageFont
# import sys
import pandas as pd
import datetime
import pygame


#Reference Data Load

# ef ---> employee data file
ef = pd.read_csv('./data-file/employee-log.csv')

valid_encodings = []
valid_ids = [] # Added this to track the IDs
valid_firstName = []
valid_lastName = []
valid_statuses = []

for index, row in ef.iterrows():
    path = row['File Name'] 
    img = face_recognition.load_image_file(path)
    encods = face_recognition.face_encodings(img)
    
    if len(encods) > 0:
        valid_encodings.append(encods[0])
        valid_ids.append(row['ID'])
        valid_firstName.append(row['First Name'])
        valid_lastName.append(row['Last Name'])
        valid_statuses.append(row['Status'])
    else:
        print(f"\nNo face detected in: {path}\n")

camera = cv2.VideoCapture(0)
for i in range(10):
    return_value, image = camera.read()
    print(return_value, image.shape) 
    cv2.imwrite('img-' + str(i) + '.png', image)            # store the image in hard disk as "img-i.png" i = 0,1,2,.....
del(camera)

uk = face_recognition.load_image_file('img-7.png')         # the middle one would be 05, but if camera not warmed up before 5, then the picture could be bit dark, so i also can pick 7, 8 or 9.
uk_encodings = face_recognition.face_encodings(uk)

if len(uk_encodings) > 0:
    uk_encoding = uk_encodings[0]
    results = face_recognition.compare_faces(valid_encodings, uk_encoding, tolerance=0.6)       # just do 0.6, 0.5 won't catch Mountain as red

    match_found = False

    for i, match in enumerate(results):
        if match:
            match_found = True
            matched_id = str(valid_ids[i])
            matched_firstName = valid_firstName[i]
            matched_lastName = valid_lastName[i]
            matched_status = valid_statuses[i]
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if matched_status == 'Denied':
                    print(f"\n RED RED RED RED RED RED RED RED RED RED RED RED  ALERT!RED RED RED RED RED RED RED RED RED RED RED RED RED ")
                    Red_entry = f"{valid_statuses[i]} {matched_firstName} {matched_lastName} {timestamp}\n"
                    with open('./data-file/RED.txt', "a") as log_file:
                        log_file.write(Red_entry) 
                    print(f"DENIED person detected: {matched_firstName} {matched_lastName}")
                    print(f"Time: {timestamp}")
                    print("Security notified.\n")
            else:
                print(f"Match found: {matched_firstName} {matched_lastName} (ID: {valid_ids[i]})")
                log_entry = f"{valid_ids[i]} {matched_firstName} {matched_lastName} {timestamp}\n"
                with open('./data-file/attendance.txt', "a") as log_file:
                    log_file.write(log_entry)    
            
            break # Stop looking once we find the first match

    if not match_found:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yellow_entry = f"UNKNOWN_USER UNKNOWN_NAME {timestamp}\n"
        with open('./data-file/Yello.txt', "a") as log_file:
            log_file.write(yellow_entry) 
        print("Alert Code-Yellow: Face detected, but no match found in the database (Unknown Person).")










    # cap = cv2.VideoCapture(0) 
    # if not cap.isOpened():
    #     print("no")
    #     exit()
    # else:
    #     print("yea")



