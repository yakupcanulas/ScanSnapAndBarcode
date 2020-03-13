image = cv2.imread('/home/pi/Desktop/Images/image' + str(i) + '.jpg')
img_rotate_clockwise = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
image = cv2.resize(img_rotate_clockwise, (800, 800))