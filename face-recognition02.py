import face_recognition
import pandas as pd

file = pd.read_csv('./data-file/data-list.csv')

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

print("---------------------------------------------------------------------------------------------------------------------")


# this has problem: because the face in picture ./Jiaqi/jiaqi-4.jpeg  can not be located first.
# this stupiud thing takes me long time to find out dam..
# so above code will only add valid encodings into de encoding list... 
# if not valid it will print out the bad one...

# import face_recognition
# import pandas as pd

# file = pd.read_csv('./FileCSV/data-list.csv')
# print(file.to_string())


# idNumber = file['ID'].tolist()
# name = file['Name'].tolist()
# fileName = file['File Name'].tolist()
# status = file['Status'].tolist()


# k = []            # k: known
# k_encod = []

# uk = face_recognition.load_image_file('./unknown/uk-00.webp', 'RGB')
# uk_encod = face_recognition.face_encodings(uk)[0]

# for i in range(len(file)):
#     k.append(face_recognition.load_image_file(fileName[i]))
#     k_encod.append(face_recognition.face_encodings(k[i]))

# fnd_status = face_recognition.compare_faces(k_encod, uk_encod, tolerance=0.5)

# print(fnd_status)


