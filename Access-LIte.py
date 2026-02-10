import face_recognition
import cv2
from PIL import ImageDraw, ImageFont
# import sys
import pandas as pd
# import datetime
import pygame


# ================================================================================================================
# PART-1: Reference Data Load
# ================================================================================================================

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
    encodings = face_recognition.face_encodings(img)
    
    if len(encodings) > 0:
        valid_encodings.append(encodings[0])
        valid_ids.append(row['ID'])
        valid_firstName.append(row['First Name'])
        valid_lastName.append(row['Last Name'])
        valid_statuses.append(row['Status'])


camera = cv2.VideoCapture(0)
for i in range(10):
    return_value, image = camera.read()
    print(return_value, image.shape) 
    cv2.imwrite('img-' + str(i) + '.png', image)            # store the image in hard disk as "img-i.png" i = 0,1,2,.....
del(camera)

uk = face_recognition.load_image_file('img-7.png')         # here i am picking the middle one, but if camera not warmed up before 07, then the picture could be bit dark, so i also can pick 08 or 09.
uk_encodings = face_recognition.face_encodings(uk)

if len(uk_encodings) > 0:
    uk_encoding = uk_encodings[0]
    results = face_recognition.compare_faces(valid_encodings, uk_encoding, tolerance=0.6)       # just do 0.6, 0.5 won't catch Mountain as red


# cap = cv2.VideoCapture(0) 
# if not cap.isOpened():
#     print("no")
#     exit()
# else:
#     print("yea")


# ==================================================================================================
# # PART-2: Reference Data Load
# # ================================================================================================================

