import face_recognition 
from PIL import Image

# photo_jiaqi_5 = face_recognition.load_image_file("./jiaqi/jiaqi-5.jpeg", "RGB")
# photo_kerr1 = face_recognition.load_image_file("./Miranda Kerr/kerr-1.jpeg", "RGB")
# photo_zhanghe1 = face_recognition.load_image_file("./ZhangHe/zhanghe-1.jpeg", "RGB")
# photo_JP1 = face_recognition.load_image_file("./JPhonex/JP-01.webp", "RGB")
# photo_strangers = face_recognition.load_image_file("./random-photos/strangers-01.jpg", "RGB")
# photo_jiaqi3 = face_recognition.load_image_file("./jiaqi/jiaqi-5.jpeg", "RGB")
# photo_jiaqi1 = face_recognition.load_image_file("./jiaqi/jiaqi-1.jpg", "RGB")

# # print(photo_JP1.shape)
# # pil_jp1 = Image.fromarray(photo_JP1)
# # pil_jp1.show()

# encode_jiaqi5 = face_recognition.face_encodings(photo_jiaqi_5)[0] # just single face
# encode_kerr1 = face_recognition.face_encodings(photo_kerr1)[0] # just single face
# encode_zhanghe1 = face_recognition.face_encodings(photo_zhanghe1)[0] # just single face
# encode_JP1 = face_recognition.face_encodings(photo_JP1)[0] # just single face
# encode_jiaqi3 = face_recognition.face_encodings(photo_jiaqi3)[0]
# encode_jiaqi1 = face_recognition.face_encodings(photo_jiaqi1)[0]

# encode_strangers = face_recognition.face_encodings(photo_strangers)[1]

# faceEncodesList = [encode_jiaqi5, encode_kerr1, encode_zhanghe1, encode_JP1, encode_jiaqi5]

# print("The distance between encode_jiaqi5 to each faces in the encoding list are: ")
# print(face_recognition.face_distance(faceEncodesList, encode_jiaqi5 ))

# print("The distance between photo_strangers to each faces in the encoding list are: ")
# print(face_recognition.face_distance(faceEncodesList, encode_strangers ))

# # print("The distance between 2 encodings: ")
# print(face_recognition.face_distance([encode_jiaqi5], encode_zhanghe1))

# print("Distance between different photo of same person: ")
# print(face_recognition.face_distance([encode_jiaqi3], encode_jiaqi1))

#==============================================================#==============================================================

n = 3
photo_taylor = []
encode_taylor = []

photo_adele = []
encode_adele = []

for i in range(n):
    pathList_taylor = f'./Taylor Swift/Taylor-0{i}.webp'
    img_taylor = face_recognition.load_image_file(pathList_taylor,'RGB')
    encode_taylor.append(face_recognition.face_encodings(img_taylor)[0])

    pathList_adele = f'./Adele/Adele-0{i}.webp'
    img_adele = face_recognition.load_image_file(pathList_adele, 'RGB')
    encode_adele.append(face_recognition.face_encodings(img_adele)[0])

for i in range (3):
# taylor[i] to adele[i]:
    a = f"The distance between each Taylor-0{i} to each Adele-0{i} in their encoding lists:"
    print(a)
    distances = face_recognition.face_distance(encode_taylor, encode_adele[i])
    print(distances)
print("------------------------------------------------------------------------------------")

for i in range (3):
# each taylor[i] to entire adele:
    b = f"The distance between Taylor-0{i} to each Adele in their encoding lists:"
    print(b)
    distances_b = face_recognition.face_distance(encode_taylor[i], encode_adele)
    print(distances_b)
print("------------------------------------------------------------------------------------")
