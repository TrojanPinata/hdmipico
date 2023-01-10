import cv2
import numpy as np
import matplotlib
import serial
import time
import os

# Notes: Less than 480p is not supported currently because it is not realistic unless for debugging purposes.
# Interlacing is also not supported yet as it is harder to configure for digital devices.
# PAL is not supported because I do not own a PAL screen.
# Test File: tokyo.mp4, 0, 0, 0

def determineWidth(HEIGHT_SETTING, DISPLAY_RATIO):
   HEIGHT_LIST = [480, 720, 1080, 1440]
   STANDARD_WIDTH = [640, 960, 1440, 1920]
   WIDESCREEN_WIDTH = [848, 1280, 1920, 2560]

   HEIGHT = HEIGHT_LIST[int(HEIGHT_SETTING)]
   if (int(DISPLAY_RATIO) == 0):
      WIDTH = STANDARD_WIDTH[int(HEIGHT_SETTING)]
   else: 
      WIDTH = WIDESCREEN_WIDTH[int(HEIGHT_SETTING)]
   
   return(HEIGHT, WIDTH)

def resizeSplit(video, WIDTH, HEIGHT):
   # preload frame
   call, image = video.read()
   counter = 0
   length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

   while call:
      if (counter == length - 1):
         break
      call, image = video.read()
      resize = cv2.resize(image, (WIDTH, HEIGHT))
      cv2.imwrite("frames\\%04d.jpg" % counter, resize)
      if cv2.waitKey(10) == 27:
         break
      counter += 1
   
   return(call, counter)

def pixelHex(WIDTH, HEIGHT, FRAME_COUNT):
   bigMatrix = []
   for k in range(FRAME_COUNT):
      img = cv2.imread("frames\\%04d.jpg" % k)
      smallMatrix = []
      for i in range(HEIGHT):
         for j in range(WIDTH):
            pixel = img[i][j]
            # hexpixel = matplotlib.colors.to_hex(pixel)
            hexpixel = '%02x%02x%02x'
            smallMatrix.append(hexpixel)
      bigMatrix.append(smallMatrix)
   return bigMatrix

def saveOutput(framedata): # WHERE WE LEFT OFF ON THE LAST EPISODE OF DRAGON BALL Z
      export = open('output.txt', 'w')
      export.write(framedata)
      export.close()
      return(True)

def initializeSerial(FC, HEIGHT, WIDTH, ilace, ser):
   ser.write(bytes('COMPUTER'))
   MESSAGE = ilace + FC + HEIGHT + WIDTH
   while (ready != True):
      check = ser.read()
      if (check == b'O'):  # 'O' is last character in pico intialization
         print("Serial ready. Sending initializer...\n")
         ser.write(bytes('1', 'ASCII')) # initialize
         print("  Awaiting response...\n")
      if (check == bytes('2', 'ASCII')):
         ready = True
         print("Response received. Sending header...\n")
         ser.write(bytes(MESSAGE, 'ASCII'))
         print("  Awaiting response...\n")
      if (check == b'y'):
         print("Ready to send.")

   return(True)

def modifyDigits(WIDTH, HEIGHT):
   d = HEIGHT
   h = WIDTH
   c = 0
   while d > 0:
      d = int(d/10)
      c += 1

   c = 0
   while h > 0:
      h = int(h/10)
      c += 1

   if d < 4:
      M_HEIGHT = "0" + str(HEIGHT)
   else:
      M_HEIGHT = str(HEIGHT)

   if h < 4:
      M_WIDTH = "0" + str(WIDTH)
   else:
      M_WIDTH = str(WIDTH)

   return(M_WIDTH, M_HEIGHT)

def modifyFC(FRAME_COUNT):
   fc = FRAME_COUNT
   c = 0
   while fc > 0:
      fc = int(fc/10)
      c += 1
   
   g = 8 - fc
   while g > 0:
      M_FC = "0" + M_FC
      g -= 1
   
   M_FC += str(FRAME_COUNT)
   return(M_FC)

def sendSerial(framedata, FRAME_COUNT, HEIGHT, WIDTH, PIXELS, ser):
   h_counter = 0
   for p in range(FRAME_COUNT):
      w_counter = 0
      for u in range(PIXELS):
         ser.write(framedata[p][u])
         w_counter += 1
         if (w_counter == (WIDTH - 1)):
            ready = False
            while (ready != True):
               check = ser.read()
               if (check == bytes('K', 'ASCII')):
                  ready = True
      h_counter += 1
      if ((w_counter == (WIDTH - 1)) and (h_counter == (HEIGHT - 1))):
            ready = False
            while (ready != True):
               check = ser.read()
               if (check == bytes('P', 'ASCII')):
                  ready = True
   return(True)

# -------------------------------------------------------------------------------------------------

def main():
   GRAYSCALE = False
   SAVE = True
   BAUDRATE = 115200
   PORT = "COM6"  # CHANGE THIS

   VIDEO_PATH = input("Input video path:")
   HEIGHT_SETTING = input("What is your desired output frame height (480p = 0, 720p = 1, 1080p = 2, 1440p = 3): ")
   DISPLAY_RATIO = input("What is the display ratio (4:3 = 0, 16:9 = 1): ")
   INTERLACE = input("Is the should the output be interlaced (Yes = 1, No = 0): ")

   HEIGHT, WIDTH = determineWidth(HEIGHT_SETTING, DISPLAY_RATIO)
   PIXELS = WIDTH * HEIGHT

   video = cv2.VideoCapture(VIDEO_PATH)
   call, FRAME_COUNT = resizeSplit(video, WIDTH, HEIGHT)
   print("Video has been resized to %sp and split into frames in the frames directory\n" % (str(HEIGHT)))
   print("Frames will now be converted into color/pixel data in order to send to serial device\n")

   framedata = pixelHex(WIDTH, HEIGHT, FRAME_COUNT)

   if SAVE == True:
      success1 = saveOutput(framedata)
      if success1 == True:
         print("Frame data saved successfully\n")
      else:
         print("There was a problem saving the frame data\n")

   ser = serial.Serial(PORT, BAUDRATE)

   M_WIDTH, M_HEIGHT = modifyDigits(WIDTH, HEIGHT)
   M_FC = modifyFC(FRAME_COUNT)

   if INTERLACE == True:
      ilace = "0001"
   else:
      ilace = "0000"

   while success2 == False:
      success2 = initializeSerial(M_FC, M_HEIGHT, M_WIDTH, ilace, ser)
      if success2 == False:
         print("There was a problem connecting to the serial device\n")

   EOV = sendSerial(framedata, FRAME_COUNT, HEIGHT, WIDTH, PIXELS, ser)


if __name__=="__main__":
   main()