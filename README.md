Running HDMI on a Raspberry Pi Pico (sort of)
=============================================
![](https://i.imgur.com/v8TTk0P.jpg)


Steps to recreate
------------------

- Clone [PicoDVI](https://github.com/Wren6991/PicoDVI)
- Drop processed header into assets folder
- Change 'testcard' to name in main.c
- Drop main.c into hello_dvi file
- Compile with cmake and pico-sdk
- Cry

Note: adapt.py is kinda broken, but will break only after outputting image. Must be run in anaconda

![](https://i.imgur.com/hhXTVRU.jpg)

DVI sock connection design from [Adafruit](https://www.adafruit.com/product/4984)