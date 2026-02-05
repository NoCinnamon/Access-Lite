from PIL import Image, ImageFilter, ImageDraw, ImageFont
import face_recognition

# # photo_jiaqi_1 = face_recognition.load_image_file('./Jiaqi/jiaqi-1.JPG', 'RGB') 
# photo_jiaqi_1 = face_recognition.load_image_file('./Jiaqi/jiaqi-1.JPG', 'L') 
# photo_zhanghe_1 = face_recognition.load_image_file('./ZhangHe/zhanghe-1.jpeg', 'RGB') 
# photo_kerr_1 = face_recognition.load_image_file('./Miranda Kerr/kerr-1.jpeg', 'RGB') 

# # photo shape print:
# print(photo_jiaqi_1.shape)
# print(photo_zhanghe_1.shape)
# print(photo_kerr_1.shape)


# # PIL image open, image filter: (import Image, ImageFilter)
# pil_jiaqi_1 = Image.open('./Jiaqi/jiaqi-1.JPG')
# pil_jiaqi_1.show()
# pil_jiaqi_1_blur = pil_jiaqi_1.filter(ImageFilter.BLUR()) # ImageFilter.BLUR()
# pil_jiaqi_1_blur.show()  # pil_jiaqi_1_emboss.show()


# # PIL image draw: (import Image, ImageDraw, ImageFont)
# pil_photo_kerr_1 = Image.open('./Miranda Kerr/kerr-1.jpeg')
# draw = ImageDraw.Draw(pil_photo_kerr_1)  # this is the drawing board
# draw.rectangle((100, 300, 250, 500), outline = (0,255,0), width = 10)
# draw.line((100, 300, 250, 500), fill = (0, 0, 255), width = 5)
# pil_photo_kerr_1.show()

# pil_photo_zhanghe_1 = Image.open('./ZhangHe/zhanghe-1.jpeg')
# draw = ImageDraw.Draw(pil_photo_zhanghe_1)  # this is the drawing board
# draw.rectangle((100, 300, 250, 500), outline = (0,255,0), width = 10)
# draw.line((100, 300, 250, 500), fill = (0, 0, 255), width = 5)
# # pil_photo_zhanghe_1.show()

# # PIL image font: (import Image, ImageDraw, ImageFont)
# # pil_photo_zhanghe_1 = Image.open('./ZhangHe/zhanghe-1.jpeg')
# fnt = ImageFont.truetype("Pillow/fonts/Arial", 40)
# draw.text((300, 260), "I love Jiaqi!", font=fnt, fill=(235, 52, 125))
# pil_photo_zhanghe_1.show()

# # Image.fromarray():
# photo_jiaqi_2 = face_recognition.load_image_file('./Jiaqi/jiaqi-2.JPG', 'RGB') 
# print(photo_jiaqi_2.shape)
# pil_image_jiaqi_2 = Image.fromarray(photo_jiaqi_2)
# pil_image_jiaqi_2.show()

# # Face location: (locate the face)
# photo_jiaqi_3 = face_recognition.load_image_file('./Jiaqi/jiaqi-3.jpeg', 'RGB')
# print(photo_jiaqi_1.shape)
# l = face_recognition.face_locations(photo_jiaqi_3)
# print(l)
# top = l[0][0]
# right = l[0][1]
# bottom = l[0][2]
# left = l[0][3]
# jiaqi_3_face = photo_jiaqi_3[top:bottom, left:right]
# print(jiaqi_3_face.shape)
# image_jiaqi_3 = Image.fromarray(jiaqi_3_face)
# image_jiaqi_3.show()


# # locate all faces in the image, show faces one by one.
# photo_two_face = face_recognition.load_image_file('./jiaqi/two-face-01.jpeg', 'RGB')
# face_locations = face_recognition.face_locations(photo_two_face)
# print("There are {} faces in this photo".format(len(face_locations)))

# face_count = 0
# for face_location in face_locations:
#     face_count += 1
#     top, right, bottom, left = face_location
#     print("Face {}   top: {}, left: {}, bottom {}, right: {}".format(face_count, top, left, bottom, right)) 
#     face_image = photo_two_face[top:bottom, left:right]
#     pil_image_two_face = Image.fromarray(face_image)
#     pil_image_two_face.show()


# show rangtangle mark on all faces in the image:
photo_two_face = face_recognition.load_image_file('./jiaqi/two-face-02.jpeg', 'RGB') # turn to numpy
face_locations = face_recognition.face_locations(photo_two_face)
# numpy array to a PIL Image so we can draw on it
pil_two_face_image = Image.fromarray(photo_two_face)

draw = ImageDraw.Draw(pil_two_face_image)
for face_location in face_locations:
    top, right, bottom, left = face_location
    
    draw.rectangle([left, top, right, bottom], outline = (0, 255, 0), width = 6)    # match what PIL expects: [left, top, right, bottom]
    pil_two_face_image.show()


# draw rectangle mark on one faces and add text onto it:
# jiaqi-6jpeg wont work, the face_recongnition library failed to find face.
# so have a good clear picture is important for this model.
photo_jiaqi_7 = face_recognition.load_image_file('./jiaqi/jiaqi-7.jpeg', 'RGB')
l= face_recognition.face_locations(photo_jiaqi_7)

top = l[0][0]
right = l[0][1]
bottom = l[0][2]
left = l[0][3]

pil_jiaqi_7 = Image.fromarray(photo_jiaqi_7)

fnt = ImageFont.truetype("Pillow/fonts/Arial", 40)

draw = ImageDraw.Draw(pil_jiaqi_7)
draw.rectangle([left, top, right, bottom], outline = (0,255,0), width = 6)
draw.text((left + 120, bottom - 50), "jiaqi", font = fnt, fill = (0,0,255))
pil_jiaqi_7.show()


# mark the count number onto rectangle box draw on each faces:
photo_strangers = face_recognition.load_image_file('./random-photos/strangers-01.jpg', 'RGB')
fl = face_recognition.face_locations(photo_strangers)

pil_strangers = Image.fromarray(photo_strangers)

face_count = len(fl)
if face_count == 0:
    print("No face found")
else:
    print("Number of Faces detected in this photo:", face_count)


fnt = ImageFont.truetype("Pillow/fonts/Arial", 40)
draw = ImageDraw.Draw(pil_strangers)

for i in range(face_count):
    top, right, bottom, left = fl[i]
    draw.rectangle(
        [left, top, right, bottom], 
        outline = (0,255,0), 
        width = 6
    )
    draw.text(
        (left+20, bottom-50), str(i), font = fnt, fill = (0,0,255)
    )
pil_strangers.show()