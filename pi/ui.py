import cv2
import time

#Load the face recognition model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") 
print(face_cascade)

#Open the web cam
cap = cv2.VideoCapture(0)

def main():

    text_queue = []
    queue_length = 10

    wait_start  = None

    while True:
        ret, img = cap.read()

        #Get the biggest face to display
        max_face = get_max_face(img)
    
        if max_face is None:
            display_text = "Look straight Into The Mirror"
        else: 
            (x,y,w,h) = max_face

            if w < 256 or h < 256:
                display_text = "Come closer"

            else:
                display_text = "Wait one second"

        text_queue.append(display_text)
        if len(text_queue) > queue_length:
            text_queue.pop(0)

        smoothed_text = most_frequent(text_queue)
        if smoothed_text == "Wait one second":
            if wait_start == None:
                wait_start = time.time()
            if time.time() - wait_start > 1:
                break


        put_text(img,smoothed_text)
        cv2.imshow("Deep Grave",img)
        cv2.waitKey(1)

def most_frequent(List): 
    counter = 0
    num = List[0] 
      
    for i in List: 
        curr_frequency = List.count(i) 
        if(curr_frequency> counter): 
            counter = curr_frequency 
            num = i 
  
    return num 

def get_max_face(img):
    to_return = None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    faces = face_cascade.detectMultiScale(gray, 1.3, 5) 
    
    for (x,y,w,h) in faces: 
        if to_return is None or w * h > to_return[3]*to_return[2]:
            to_return = (x,y,w,h)
        # To draw a rectangle in a face  
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,255,0),2)

    return to_return

def put_text(img,text):
    font                   = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (10,500)
    fontScale              = 1
    fontColor              = (255,255,255)
    lineType               = 2

    cv2.putText(img,text, 
        bottomLeftCornerOfText, 
        font, 
        fontScale,
        fontColor,
        lineType)

main()