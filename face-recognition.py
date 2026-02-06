import face_recognition
# from PIL import Image


# # Compare 2 faces
# img_jiaqi = face_recognition.load_image_file('./jiaqi/jiaqi-3.jpeg', 'RGB')
# encode_jiaqi = face_recognition.face_encodings(img_jiaqi)[0]

# img_uk = face_recognition.load_image_file('./unknown/uk-00.webp', 'RGB')
# encode_uk = face_recognition.face_encodings(img_uk)[0]
# # image_uk = Image.fromarray(img_uk)
# # image_uk.show()

# fnd_result = face_recognition.compare_faces([encode_jiaqi], encode_uk, tolerance=0.5)   # if the tolerance is not specified in the face_recognition.compare_faces method, it defaults to a value of 0.6. 
# print(fnd_result)
# if fnd_result[0]:
#     print("This is Jiaqi, Pass")
# else:
#     print("This is not Jiaqi. Fail")
    

print("------------------------------------------------------------------------------------")


f0 = face_recognition.load_image_file('./Taylor Swift/Taylor-00.webp', 'RGB')
f1 = face_recognition.load_image_file('./Taylor Swift/Taylor-01.webp', 'RGB')
f2 = face_recognition.load_image_file('./Taylor Swift/Taylor-02.webp', 'RGB')
f3 = face_recognition.load_image_file('./Taylor Swift/Taylor-03.webp', 'RGB')
fuk = face_recognition.load_image_file('./Miranda Kerr/kerr-1.jpeg', 'RGB')

f0_enco = face_recognition.face_encodings(f0)[0]
f1_enco = face_recognition.face_encodings(f1)[0]
f2_enco = face_recognition.face_encodings(f2)[0]
f3_enco = face_recognition.face_encodings(f3)[0]
fuk_enco = face_recognition.face_encodings(fuk)[0]

faces = [f0_enco, f1_enco, f2_enco, f3_enco]

fnd_result = face_recognition.compare_faces(faces, fuk_enco)
print(fnd_result)

for i, match in enumerate(fnd_result):
    print(f"Face unknown compared to f{i}: {match}")


print("------------------------------------------------------------------------------------")



# 1. Load and Encode "Green List" (Authorized)
f0 = face_recognition.load_image_file('./Adele/Adele-00.webp')
f1 = face_recognition.load_image_file('./JPhonex/JP-01.webp')
f2 = face_recognition.load_image_file('./Jiaqi/jiaqi-7.jpeg')
f3 = face_recognition.load_image_file('./random-photos/strangers-01.jpg')
f4 = face_recognition.load_image_file('./Taylor Swift/Taylor-06.jpg')


f0_enco = face_recognition.face_encodings(f0)[0]
f1_enco = face_recognition.face_encodings(f1)[0]
f2_enco = face_recognition.face_encodings(f2)[0]
f3_enco = face_recognition.face_encodings(f3)[0]
f4_enco = face_recognition.face_encodings(f4)[0]



green_list = [f0_enco, f1_enco, f2_enco, f3_enco, f4_enco]

# 2. Load and Encode "Red List" (Denied)
fred = face_recognition.load_image_file('./red-list/Mountain.jpg')
fred_enco = face_recognition.face_encodings(fred)[0]
red_list = [fred_enco]

# 3. Process the Unknown Face
# fuk = face_recognition.load_image_file('./unknown/uk-00.webp')
# fuk_enco = face_recognition.face_encodings(fuk)[0] # Single encoding, not a list!

fuk01 = face_recognition.load_image_file('./unknown/Taylor-05.webp')
fuk01_enco = face_recognition.face_encodings(fuk01)[0] # Single encoding, not a list!


# 4. Compare against both lists
green_matches = face_recognition.compare_faces(green_list, fuk01_enco)
red_matches = face_recognition.compare_faces(red_list, fuk_enco)

if any(green_matches):
    print("STATUS: GREEN LIST (Access Granted)")
    # Logic to log attendance or unlock door here
elif any(red_matches):
    print("STATUS: RED LIST (Access Denied - Security Alert!)")
    # Logic to send Slack/Email notification here
else:
    print("STATUS: UNKNOWN (Access Denied)")

# 6. Detailed Loop (to see exactly which face matched)
for i, match in enumerate(green_matches):
    print(f"Comparison with Green List face #{i}: {match}")


# print("------------------------------------------------------------------------------------")

# for udmy assignment:
# f0 = face_recognition.load_image_file('./Jiaqi/jiaqi-1.jpg')
# f1 = face_recognition.load_image_file('./Adele/Adele-03.webp', 'RGB')

# fuk = face_recognition.load_image_file('./Jiaqi/jiaqi-5.jpeg', 'RGB')

# f0_enco = face_recognition.face_encodings(f0)[0]
# f1_enco = face_recognition.face_encodings(f1)[0]
# fuk_enco = face_recognition.face_encodings(fuk)[0]

# faces = [f0_enco, f1_enco]

# fnd_result = face_recognition.compare_faces(faces, fuk_enco)

# for i, match in enumerate(fnd_result):
#     print(f"Face unknown compared to f{i}: {match}")