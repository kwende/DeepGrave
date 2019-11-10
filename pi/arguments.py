import argparse

def parsed_args():
    # construct the argument parser and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-r","--rotation",default=0,type=int,choices=[0,90,180,270])
    parser.add_argument("-p", "--picamera", type=int, default=-1, help="whether or not the Raspberry Pi camera should be used")
    parser.add_argument("-hf", "--horizontalflip", type=bool, default=False, help="Flip the image horizontally")
    parser.add_argument("-vf", "--verticalflip", type=bool, default=False, help="Flip the image vertically")
    parser.add_argument("--minfacesize", type=int, default=256, help="Min detected face size in the original image")
    parser.add_argument("--zombietime", type=float, default=5, help="Min detected face size in the original image")
    parser.add_argument("-f","--fontsize", type=int, default=128, help="Min detected face size in the original image")


    return parser.parse_args()