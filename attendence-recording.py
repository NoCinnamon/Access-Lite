import face_recognition
import datetime 
import pandas as pd

file = pd.read_csv('./data-File/data-list.csv')

# Use these to keep only the valid data
valid_encodings = []
valid_names = []

uk = face_recognition.load_image_file('./unknown/uk-00.webp', 'RGB')
uk_encodings = face_recognition.face_encodings(uk)

if len(uk_encodings) > 0:
    uk_encod = uk_encodings[0]

    for i in range(len(file)):
        path = file['File Name'].tolist()[i]
        img = face_recognition.load_image_file(path)
        encods = face_recognition.face_encodings(img)
        
        if len(encods) > 0:
            valid_encodings.append(encods[0])
            valid_names.append(file['Name'].tolist()[i])
        else:
            print(f"\nNo face detected : {path}\n")

    fnd_status = face_recognition.compare_faces(valid_encodings, uk_encod, tolerance=0.5)
    
    print("Comparison Results (True/False):")
    print(fnd_status)
    print("")
  


    # See who actually matched:
    for i, match in enumerate(fnd_status):
        if match:
            print(f"Match found! This is {valid_names[i]}\n")
    
    
    
else:
    print("Could not find a face in the unknown image.\n")

print (found)
for i in range(len(file)):
    if fnd_status[i]:
        x= str(datetime.datetime.now)

        attend = "\n"+str(k[i])+" "+str(name[i]+" "+x)
        f = open("./Data File/Attendance.txt", "a")
        f.write(attend)
        f.close()

    
