import face_recognition
# from PIL import Image


# Compare 2 faces
img_jiaqi = face_recognition.load_image_file('./jiaqi/jiaqi-3.jpeg', 'RGB')
encode_jiaqi = face_recognition.face_encodings(img_jiaqi)[0]

img_uk = face_recognition.load_image_file('./unknown/uk-00.webp', 'RGB')
encode_uk = face_recognition.face_encodings(img_uk)[0]
# image_uk = Image.fromarray(img_uk)
# image_uk.show()

compare_result = face_recognition.compare_faces([encode_jiaqi], encode_uk, tolerance=0.5)
if compare_result[0]:
    print("This is Jiaqi, Pass")
else:
    print("This is not Jiaqi. Fail")
    