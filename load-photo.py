from PIL import Image, ImageFilter, ImageDraw, ImageFont
import face_recognition

# photo_jiaqi_1 = face_recognition.load_image_file('./Jiaqi/jiaqi-1.JPG', 'RGB') 
photo_jiaqi_1 = face_recognition.load_image_file('./Jiaqi/jiaqi-1.JPG', 'L') 

photo_zhanghe_1 = face_recognition.load_image_file('./ZhangHe/zhanghe-1.jpeg', 'RGB') 
photo_kerr_1 = face_recognition.load_image_file('./Miranda Kerr/kerr-1.jpeg', 'RGB') 

# photo shape print:
print(photo_jiaqi_1.shape)
print(photo_zhanghe_1.shape)
print(photo_kerr_1.shape)

# PIL image open, image filter: (import Image, ImageFilter)
pil_jiaqi_1 = Image.open('./Jiaqi/jiaqi-1.JPG')
pil_jiaqi_1.show()
pil_jiaqi_1_blur = pil_jiaqi_1.filter(ImageFilter.BLUR()) # ImageFilter.BLUR()
pil_jiaqi_1_blur.show()  # pil_jiaqi_1_emboss.show()


# PIL image draw: (import Image, ImageDraw, ImageFont)
pil_photo_kerr_1 = Image.open('./Miranda Kerr/kerr-1.jpeg')
draw = ImageDraw.Draw(pil_photo_kerr_1)  # this is the drawing board
draw.rectangle((100, 300, 250, 500), outline = (0,255,0), width = 10)
draw.line((100, 300, 250, 500), fill = (0, 0, 255), width = 5)
pil_photo_kerr_1.show()

pil_photo_zhanghe_1 = Image.open('./ZhangHe/zhanghe-1.jpeg')
draw = ImageDraw.Draw(pil_photo_zhanghe_1)  # this is the drawing board
draw.rectangle((100, 300, 250, 500), outline = (0,255,0), width = 10)
draw.line((100, 300, 250, 500), fill = (0, 0, 255), width = 5)
# pil_photo_zhanghe_1.show()

# PIL image font: (import Image, ImageDraw, ImageFont)
# pil_photo_zhanghe_1 = Image.open('./ZhangHe/zhanghe-1.jpeg')
fnt = ImageFont.truetype("Pillow/fonts/Arial", 40)
draw.text((300, 260), "I love Jiaqi!", font=fnt, fill=(235, 52, 125))
pil_photo_zhanghe_1.show()
