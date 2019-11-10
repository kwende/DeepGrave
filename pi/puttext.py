import numpy as np
from PIL import ImageFont, ImageDraw, Image
import cv2
import time

fontpath = "./Creepster-Regular.ttf"     
font = None

def put_text(img,text,font_size = 32):
    global font
    
    if font is None:
        font = ImageFont.truetype(fontpath, font_size)
    
    ## Make canvas and set the color
    b,g,r,a = 0,255,0,0

    textsize = font.getsize(text)
    textX = (img.shape[1] - textsize[0])//2
    textY = (img.shape[0] + textsize[1])//2
    bottomLeftCornerOfText = (textX,textY)
    
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)
    draw.text(bottomLeftCornerOfText,  text, font = font, fill = (b, g, r, a))
    return np.array(img_pil)
