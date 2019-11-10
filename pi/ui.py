import cv2
import time
import requests
import numpy as np
import math
from screenresolution import screen_resolution
from puttext import put_text
from arguments import parsed_args
from imutils.video import VideoStream
 
#Load the face recognition model
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
global_time = None

def sw(message):
    global global_time
    if global_time is None:
        global_time = time.time()
        print(message)
        return
    
    print(message + " " + str(time.time() - global_time))
    global_time = time.time()
    

def main():
    args = parsed_args()

    # initialize the video stream and allow the cammera sensor to warmup
    vs = VideoStream(usePiCamera=args.picamera > 0, resolution=(1920,1080)).start()
    time.sleep(2.0)

    #Set up a full sized window
    cv2.namedWindow("Deep Grave", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Deep Grave", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    screen_width, screen_height = screen_resolution()
    display_height,display_width = rotate_size((screen_height,screen_width),args.rotation)
 
    # capture frames from the camera
    while True:
        #UI for capturing image
        img = get_image(vs,args,display_width,display_height)
        if img is None:
            return

        #Turn it into a zombie picture
        zombie = deep_grave_me(img)
        if zombie is None:
            continue

        #Show it
        show_zombie(zombie,args,display_width,display_height)

def show_zombie(zombie,args,display_width,display_height):
    zombie = resize_without_data_loss(zombie,display_width,display_height)
    zombie = rotate_img(zombie,args.rotation)
    cv2.imshow("Deep Grave",zombie)

    zombie_start_time = time.time()
    while time.time() - zombie_start_time < args.zombietime:
        key = cv2.waitKey(1)
        
        if key == ord('q'):
            break

def get_image(vs,args,display_width,display_height):
    text_queue = []
    queue_length = 10
    wait_start  = None

    to_return = None

    # capture frames from the camera
    while True:
        img = vs.read()
        if img is None:
            print("Sleeping")
            time.sleep(.1)
            continue
        
        img = clip_to_display_aspect_ratio(img,display_width,display_height)
        
        if args.horizontalflip and args.verticalflip :
            img = rotate_img(img,180)
        elif args.horizontalflip:
            img = cv2.flip(img,1)
        elif args.verticalflip:
            img = cv2.flip(img,0)
        
        #ret, img = cap.read()

        #Get the biggest face to display
        
        max_face = get_max_face(img)
    
        if max_face is None:
            display_text = "Look Into The Mirror"
        else: 
            (x,y,w,h) = max_face

            if w < args.minfacesize or h < args.minfacesize:
                display_text = "Come closer"

            else:
                display_text = "Good"
                to_return = img

        text_queue.append(display_text)
        if len(text_queue) > queue_length:
            text_queue.pop(0)
            
        smoothed_text = most_frequent(text_queue)
        if smoothed_text == "Good":
            if wait_start == None:
                wait_start = time.time()
            if time.time() - wait_start > 3:
                return to_return
                
        else:
            wait_start = None

        #Create the display image
        display_image = cv2.resize(img,(display_width,display_height))
        display_image = put_text(display_image,smoothed_text,args.fontsize)
        display_image = rotate_img(display_image,args.rotation)
        
        #Display display image
        cv2.imshow("Deep Grave", display_image)
        key = cv2.waitKey(1)
        
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
    
    return None
        
def rotate_size(size,rotation):
    assert(rotation in [0,90,180,270])

    if rotation in [0,180]:
        return size
    else:
        return (size[1],size[0])

def rotate_img(img,rotation):
    assert(rotation in [0,90,180,270])
    
    if rotation == 0:
        return img
    else:
        return np.rot90(img,rotation//90)
        

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
    
    width = img.shape[1]
    height = img.shape[0]

    n_pixels = 129600 #target number of pixels
    scale = math.sqrt(width*height/n_pixels)
    small_size = (round(width/scale),round(height/scale))
    small_img = cv2.resize(img,small_size)
    gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(gray, 1.3, 5) 
    
    for (x,y,w,h) in faces: 
        if to_return is None or w * h > to_return[3]*to_return[2]:
            to_return = (x,y,w,h)
        # To draw a rectangle in a face  
        #cv2.rectangle(img,(x,y),(x+w,y+h),(255,255,0),2)
        
    if to_return is None:
        return None
    
    x,y,w,h = to_return
    x = max(min(round(x * scale),width-1),0)
    y = max(min(round(y * scale),height-1),0)
    w = min(round(w * scale),width - x)
    h = min(round(h * scale),height - y)

    return (x,y,w,h)

def put_text_cv2(img,text):
    font                   = cv2.FONT_HERSHEY_SIMPLEX
    
    fontScale              = 1
    fontColor              = (0,255,0)
    lineType               = 2
    
    textsize = cv2.getTextSize(text,font,1,2)[0]
    textX = (img.shape[1] - textsize[0])//2
    textY = (img.shape[0] + textsize[1])//2
    bottomLeftCornerOfText = (textX,textY)

    cv2.putText(img,text, 
        bottomLeftCornerOfText, 
        font, 
        fontScale,
        fontColor,
        lineType)
    
def deep_grave_me(img):
    cv2.imwrite("currentPerson.png",img)
    with open('currentPerson.png', 'rb') as f:
        r = requests.post('https://deepgrave.me/api/upload?dobinary=true', files={'currentPerson.png': f}, verify=False) 
    with open('currentZombie.png', 'wb') as zombie:
        zombie.write(r.content)
    return cv2.imread("currentZombie.png")

def resize_without_data_loss(img,new_width,new_height):
    #Figure out the new size we'll resize to 
    old_height,old_width,_ = img.shape
    scale = min(new_height/old_width,new_width/old_width)
    new_height_no_border,new_width_no_border = (round(old_height * scale),round(old_width * scale))
    new_size_without_border = (new_width_no_border,new_height_no_border)
    
    #Resize it
    to_return_without_border = cv2.resize(img,new_size_without_border)
    top = (new_height - new_height_no_border)//2
    bottom = (new_height - new_height_no_border)//2
    left = (new_width - new_width_no_border)//2
    right = (new_width - new_width_no_border)//2
    return cv2.copyMakeBorder(to_return_without_border,top,bottom,left,right,cv2.BORDER_CONSTANT,value=[0,0,0])

def clip_to_display_aspect_ratio(img, new_width, new_height):
    #Figure out the new size we'll resize to 
    old_height,old_width,_ = img.shape
    scale = max(new_height/old_height,new_width/old_width)
    original_roi_height = min(round(new_height/scale),old_height)
    original_roi_width = min(round(new_width/scale),old_width)
    top = max(0,old_height//2 - original_roi_height//2)
    bottom = min(old_height,old_height//2 + original_roi_height//2)
    left = max(0,old_width//2 - original_roi_width//2)
    right = min(old_width,old_width//2 + original_roi_width//2)
    
    return img[top:bottom,left:right,:]

main()