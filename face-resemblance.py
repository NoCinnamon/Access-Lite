import face_recognition 
from PIL import Image

photo_jiaqi_5 = face_recognition.load_image_file("./jiaqi/jiaqi-5.jpeg", "RGB")
photo_kerr1 = face_recognition.load_image_file("./Miranda Kerr/kerr-1.jpeg", "RGB")
photo_zhanghe1 = face_recognition.load_image_file("./ZhangHe/zhanghe-1.jpeg", "RGB")
photo_JP1 = face_recognition.load_image_file("./JPhonex/JP-01.webp", "RGB")
photo_strangers = face_recognition.load_image_file("./random-photos/strangers-01.jpg", "RGB")
photo_jiaqi3 = face_recognition.load_image_file("./jiaqi/jiaqi-5.jpeg", "RGB")
photo_jiaqi1 = face_recognition.load_image_file("./jiaqi/jiaqi-1.jpg", "RGB")

# print(photo_JP1.shape)
# pil_jp1 = Image.fromarray(photo_JP1)
# pil_jp1.show()

encode_jiaqi5 = face_recognition.face_encodings(photo_jiaqi_5)[0] # just single face
encode_kerr1 = face_recognition.face_encodings(photo_kerr1)[0] # just single face
encode_zhanghe1 = face_recognition.face_encodings(photo_zhanghe1)[0] # just single face
encode_JP1 = face_recognition.face_encodings(photo_JP1)[0] # just single face
encode_jiaqi3 = face_recognition.face_encodings(photo_jiaqi3)[0]
encode_jiaqi1 = face_recognition.face_encodings(photo_jiaqi1)[0]

encode_strangers = face_recognition.face_encodings(photo_strangers)[1]

faceEncodesList = [encode_jiaqi5, encode_kerr1, encode_zhanghe1, encode_JP1, encode_jiaqi5]

print("The distance between encode_jiaqi5 to each faces in the encoding list are: ")
print(face_recognition.face_distance(faceEncodesList, encode_jiaqi5 ))

print("The distance between photo_strangers to each faces in the encoding list are: ")
print(face_recognition.face_distance(faceEncodesList, encode_strangers ))

# print("The distance between 2 encodings: ")
print(face_recognition.face_distance([encode_jiaqi5], encode_zhanghe1))

print("Distance between different photo of same person: ")
print(face_recognition.face_distance([encode_jiaqi3], encode_jiaqi1))