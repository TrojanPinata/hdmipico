import cv2
import numpy as np
import matplotlib
import serial
import time
import os
import sys

# Notes: Less than 480p is not supported currently because it is not realistic unless for debugging purposes.
# (Unless using the manual override included in main())
# Interlacing is also not supported yet as it is harder to configure for digital devices.
# PAL is not supported because I do not own a PAL screen.
# A lot of the 'video' protions are broken bc the Pico can't really run long video well and I don't want to
# try and force it. Stick to images if you can.


# determine WIDTH based off of desired height and display ratio
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

# split video into frames and resize to desired dimensions
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

# convert video to hex values nested array
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

# save frame/image data once converted to hex for video
def saveOutputVideo(frameData):
   try: 
      export = open('output.txt', 'w')
   except:
      print("problem creating or opening output.txt. determine the source of the error and try again (line 67)")
      sys.exit(0)
   for k in range(len(frameData)):
      for p in range(len(frameData[k])):
         export.write(frameData[k][p])
         if ((p % 15) == 0):
            export.write("\n")
      export.write("\n")
   export.close()
   return(True)

# save frame/image data once converted to rgb565 for images
def saveOutputImage(imageData):
   try: 
      export = open('output.txt', 'w')
   except:
      print("problem creating or opening output.txt. determine the source of the error and try again (line 82)")
      sys.exit(0)
   lengthImageData = len(imageData)
   for k in range(lengthImageData):
      if (((k % 12) == 0) and (k != 0)):
         export.write("\n")
      export.write(imageData[k])
      export.write(", ")
   export.close()
   return(True)

# initialize the serial connection
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

# modify the HEIGHT and WIDTH variables to be easier to transmit
def modifyDigits(WIDTH, HEIGHT):
   # M_HEIGHT and M_WIDTH will always be 4 bytes long
   M_HEIGHT = ""
   M_WIDTH = ""
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

# modify the FRAME_COUNT variable to be easier to transmit
def modifyFC(FRAME_COUNT):
   # M_FC will always be 8 bytes long
   M_FC = ""
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

# send frame data to device. works for both images and devices when saved locally
def sendStream(frameData, FRAME_COUNT, HEIGHT, WIDTH, ser):
   h_counter = 0
   for p in range(FRAME_COUNT):
      w_counter = 0
      for u in range((WIDTH*HEIGHT)):
         ser.write(frameData[p][u])
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

def imagePixelData(image, WIDTH, HEIGHT):
   imageData = []
   R = ""
   G = ""
   B = ""
   he = []
   HU = ""
   for i in range(HEIGHT):
      for j in range(WIDTH):
         # functional bitshift
         R = (image[i,j][2]) // 8
         G = (image[i,j][1]) // 4
         B = (image[i,j][0]) // 8
         hexValue = hex((R<<11) | (G<<5) | B)
         he[:0] = hexValue
         while len(hexValue) < 6:
            he.insert(2, "0")
            hexValue = HU.join(he)
         he = []
         HU = ""
         imageData.append(hexValue[0:2] + hexValue[4:6])
         imageData.append(hexValue[0:4])
      
   return(imageData)

def sendImage(imageData, WIDTH, HEIGHT, ser, RATELIMIT):
   numBytes = len(imageData)
   numBytesCheck = 2*(WIDTH*HEIGHT)
   response = False

   if (numBytesCheck != numBytes):
      print("Check the lengths of the image data as there is a problem with the rgb565 encoding")
      sys.exit(0)

   # send data and wait for response after every 16 bytes. no CRC as to increase speed. will add if issues
   for i in range(len(imageData)):
      if (((i % 16) == 0) and (RATELIMIT == True)):
         ready = False
         while (ready != True):
            check = ser.read()
            if (check == bytes('.', 'ASCII')):
               ready = True
      else:
         ser.write(imageData[i])
   ser.write("FINISHED")
   while (response != True):
      res = ser.read()
      # last character of 'THANK YOU'
      if (res == 'U'):
         response = True
   return(True)


# -------------------------------------------------------------------------------------------------

def main():
   # important flags
   GRAYSCALE = False
   SAVE = True
   BAUDRATE = 115200
   PORT = "COM6"  # CHANGE THIS
   RATELIMIT = False 

   # inputs
   IMAGEVIDEO = input("Are you inputting a image or video (Video = 1, Image = 0): ")
   VIDEO_PATH = input("Input video/image path: ")
   HEIGHT_SETTING = str(input("What is your desired output frame height (480p = 0, 720p = 1, 1080p = 2, 1440p = 3): "))
   DISPLAY_RATIO = str(input("What is the display ratio (4:3 = 0, 16:9 = 1, Same as File = 2): "))
   if (IMAGEVIDEO == "1"):
      INTERLACE = input("Is the should the output be interlaced (Video only) (Yes = 1, No = 0): ")
   else:
      INTERLACE = "0"
   STREAM = "0" #input("Stream frames or send data for local playback? (Stream = 1, Local = 0")

   # clean up inputs. 0 is always default
   if (IMAGEVIDEO != "0") or (IMAGEVIDEO != "1"):
      IMAGEVIDEO = "0"

   if (HEIGHT_SETTING != "0") or (HEIGHT_SETTING != "1"):
      HEIGHT_SETTING = "0"

   if (DISPLAY_RATIO != "0") or (DISPLAY_RATIO != "1") or DISPLAY_RATIO != "2":
      DISPLAY_RATIO = "0"
   
   if (INTERLACE != "0") or (INTERLACE != "1"):
      INTERLACE = "0"

   if (STREAM != "0") or (STREAM != "1"):
      STREAM = "0"

   HEIGHT, WIDTH = determineWidth(HEIGHT_SETTING, DISPLAY_RATIO)

   # DIMENSIONS OVERRIDE
   #HEIGHT = 240
   #WIDTH = 320
   # FRAME_COUNT = 32

   # check for video/image file
   MEDIA_PATH = os.getcwd() + VIDEO_PATH
   #if (os.path.isfile(MEDIA_PATH) == False):
      #print("media file not found")
      #sys.exit(0)

   if (IMAGEVIDEO == "0"):
      FRAME_COUNT = 1

   # fix screen dimensions for easy transmission
   M_WIDTH, M_HEIGHT = modifyDigits(WIDTH, HEIGHT)
   M_FC = modifyFC(FRAME_COUNT)

   # video is totally broken rn so don't use that ig
   if (IMAGEVIDEO == "1"):
      # fix interlace values for easy transmission
      if INTERLACE == True:
         ilace = "0001"
      else:
         ilace = "0000"

      video = cv2.VideoCapture(VIDEO_PATH)
      call, FRAME_COUNT = resizeSplit(video, WIDTH, HEIGHT)
      print("Video has been resized to %sp and split into frames in the frames directory\n" % (str(HEIGHT)))

      print("Frames will now be converted into color/pixel data in order to send to serial device\n")
      frameData = pixelHex(WIDTH, HEIGHT, FRAME_COUNT)

      # check flag then save data to output.txt (SAVE flag check is outside of function to provide success feedback)
      if SAVE == True:
         success1 = saveOutputVideo(frameData)
         if success1 == True:
            print("Frame data saved successfully\n")
         else:
            print("There was a problem saving the frame data\n")

      # start serial connection
      ser = serial.Serial(PORT, BAUDRATE)

      # initialize serial
      while success2 == False:
         success2 = initializeSerial(M_FC, M_HEIGHT, M_WIDTH, ilace, ser)
         if success2 == False:
            print("There was a problem connecting to the serial device (line 308)\n")
            sys.exit(0)
      # check for response
      sendStream(frameData, FRAME_COUNT, HEIGHT, WIDTH, ser)

   # sending single image
   else:
      print("Image data will be converted to bytes and sent to serial device\n")
      ilace = "0000"

      # it is inefficient to make serperate functions for these as bad form as it is
      # i am trying to make the steps in the video portion match the image function and vice versa
      image = cv2.imread(VIDEO_PATH)
      imageR = cv2.resize(image, (WIDTH, HEIGHT), interpolation= cv2.INTER_LINEAR)
      imageData = imagePixelData(imageR, WIDTH, HEIGHT)

      # check flag then save data to output.txt (SAVE flag check is outside of function to provide success feedback)
      if SAVE == True:
         success1 = saveOutputImage(imageData)
         if success1 == True:
            print("Image data saved successfully\n")
         else:
            # assumes problem occurs while saving and not an IOError
            print("There was a problem saving the image data (line 331)\n")

      # start serial connection
      ser = serial.Serial(PORT, BAUDRATE)

      while success2 == False:
         success2 = initializeSerial(M_FC, M_HEIGHT, M_WIDTH, ilace, ser)
         if success2 == False:
            print("There was a problem connecting to the serial device\n")
            sys.exit(0)

      sendImage(imageData, WIDTH, HEIGHT, ser, RATELIMIT)

if __name__=="__main__":
   main()