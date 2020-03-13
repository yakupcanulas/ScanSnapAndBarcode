import cv2
import numpy as np
from fpdf import FPDF
from os import listdir
import RPi.GPIO as GPIO
import datetime
from pyzbar.pyzbar import decode
import time

#cap2 = cv2.VideoCapture(1)
cap = cv2.VideoCapture(0)

GPIO.setmode(GPIO.BOARD)

GPIO.setup(36,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(31,GPIO.IN, pull_up_down=GPIO.PUD_UP)

ledpinAcik = 7
ledpinKapali = 11

GPIO.setup(ledpinAcik, GPIO.OUT)
GPIO.setup(ledpinKapali, GPIO.OUT)


def rectify(h):
    h = h.reshape((4, 2))
    hnew = np.zeros((4, 2), dtype=np.float32)

    add = h.sum(1)
    hnew[0] = h[np.argmin(add)]
    hnew[2] = h[np.argmax(add)]

    diff = np.diff(h, axis=1)
    hnew[1] = h[np.argmin(diff)]
    hnew[3] = h[np.argmax(diff)]

    return hnew


def barcodeReader(image, bgr):
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    barcodes = decode(gray_img)

    for decodedObject in barcodes:
        points = decodedObject.polygon

        pts = np.array(points, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, (0, 255, 0), 3)

    for bc in barcodes:
        cv2.putText(frame, bc.data.decode("utf-8") + " - " + bc.type, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    bgr, 2)

        return "Barcode: {} - Type: {}".format(bc.data.decode("utf-8"), bc.type)

bgr = (8, 70, 208)


i = 0

while True:

    while True:
        ret, frame = cap.read()
        #ret, frame2 = cap2.read()
        cv2.imshow("AnaResim", frame)
        #cv2.imshow("Deneme", frame2)
        key = cv2.waitKey(30)
        

        if GPIO.input(31) == 0:
            
            GPIO.output(ledpinAcik, True)
            time.sleep(0.5)
            GPIO.output(ledpinAcik, False)
            
            i += 1
            
            while i != 0:

                #cv2.imshow("YakalananResim", frame)
                cv2.imwrite('/home/pi/Desktop/Images/image' + str(i) + '.jpg', frame)

                print("Fotograf Kaydedildi...")
                barcode = barcodeReader(frame, bgr)
                print(barcode)

                dosya = open('/home/pi/Desktop/Barkod/Barkod' + str(i) + '.txt', "w")
                print(barcode, file=dosya)
                # dosya.close()
                
                break
            
            

        elif GPIO.input(36) == 0:
            
            GPIO.output(ledpinKapali, True)
            time.sleep(0.5)
            GPIO.output(ledpinKapali, False)

            while i != 0:
                #rotate kısmı buraya eklenecek masaüstünde mevcut
                #image = cv2.imread('/home/pi/Desktop/Images/image' + str(i) + '.jpg')
                #image = cv2.resize(image, (960, 720)) bu kısım önemli

                image = cv2.imread('/home/pi/Desktop/Images/image' + str(i) + '.jpg')
                img_rotate_clockwise = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                image = cv2.resize(img_rotate_clockwise, (1920, 1080))

                orig = image.copy()

                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)

                edged = cv2.Canny(blurred, 0, 50)
                orig_edged = edged.copy()

                (_ ,contours, _) = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                for c in contours:
                    p = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.02 * p, True)

                    if len(approx) == 4:
                        target = approx

                        break

                approx = rectify(target)
                pts2 = np.float32([[0, 0], [800, 0], [800, 800], [0, 800]])

                M = cv2.getPerspectiveTransform(approx, pts2)
                dst = cv2.warpPerspective(orig, M, (800, 800))
                cv2.drawContours(image, [target], -1, (0, 255, 0), 2)
                dst = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
                #T = threshold_local(dst, 51, offset=9, method = "gaussian")
                #dst = (dst > T).astype("uint8") * 255

                #cv2.imshow("YesilKenar.jpg", image)
                cv2.imshow("Hedef.jpg", dst)
                cv2.imwrite('/home/pi/Desktop/CropImages/image' + str(i) + '.jpg', dst)

                i -= 1

            break
        
        
    path = "/home/pi/Desktop/CropImages/"

    imagelist = listdir(path)

    pdf = FPDF('P', 'mm', 'A4')

    x, y, w, h = 0, 0, 210, 297

    for image in imagelist:
        pdf.add_page()
        pdf.image(path + image, x, y, w, h)

    tarih = datetime.datetime.now()
    t1 = tarih.strftime("%d")
    t2 = tarih.strftime("%b")
    t3 = tarih.strftime("%Y")
    t4 = tarih.strftime("%H")
    t5 = tarih.strftime("%M")
    t6 = tarih.strftime("%S")

    dosyaadi = "/home/pi/Desktop/PDFhazir/" + str(t1 + t2 + t3 + t4 + t5 + t6) + ".pdf"
    pdf.output(dosyaadi, 'F')

    j = 99

    while 0 < j < 100:
        try:
            cv2.os.remove('/home/pi/Desktop/Images/image' + str(j) + '.jpg')
            cv2.os.remove('/home/pi/Desktop/CropImages/image' + str(j) + '.jpg')
        except:
            pass
        j -= 1

    print("PDF'e dönüştürme ve Barkod okuma işlemi başarılı bir şekilde tamamlanmıştır...")

    continue

GPIO.cleanup()

    #cv2.waitKey(0)

    #if key == ord('m'):
        #cv2.destroyAllWindows()
