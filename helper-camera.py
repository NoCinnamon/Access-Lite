import cv2
# print(cv2.__version__)

camera = cv2.VideoCapture(0)                                # The camera variable typically refers to an object created to access the camera hardware via OpenCV. 
for i in range(10):
    return_value, image = camera.read()
    print(return_value, image.shape()) 
    cv2.imwrite('img-' + str(i) + '.png', image)           # store the image in hard disk as "img-i.png" i = 0,1,2,.....

del(camera)