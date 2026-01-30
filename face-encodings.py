import face_recognition

photo_twoFace = face_recognition.load_image_file("./jiaqi/two-face-01.jpeg", "RGB")
encode_twoFace = face_recognition.face_encodings(photo_twoFace)

print("The number of faces: ", len(encode_twoFace))
print("The shape of encodings for each face detacted: ", encode_twoFace[0].shape)       # [0] here just to show the 128 this number, because each encoding is a vector of 128 numbers
print("Print out all the encodings: ")
for i in range(len(encode_twoFace)):
    print(i)
    print(encode_twoFace[i])                # here is the actual encodings print out for each face detacted.



