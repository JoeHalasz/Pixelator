import sys

import numpy as np
import imageio.v2 as iio
import threading
import time

imageInputPath = "images/"
imageOutputPath = "output/"

def timeIt(numDown, numToDo, lastPercentDone, timeAtStart):
    percentDone = (numDown / numToDo) * 100
    if (int(percentDone) != lastPercentDone):
        timeTaken = time.time() - timeAtStart
        estimatedTimeTotal = timeTaken*(1/(percentDone/100))
        print('\r' + str(int(percentDone)) + "%, time remaining:", round(estimatedTimeTotal - timeTaken,2), "seconds", end='', flush=True)
    return int(percentDone)

def getColorPalletForced():
    # open file colorPallet.txt
    colorPallet = set()
    with open("colorPallet.txt", "r") as file:
        for line in file:
            try:
                color = line.split(",")
                if (len(color) == 3):
                    color.append(255)
                newColor = (int(color[0]), int(color[1]), int(color[2]), int(color[3]))
                for c in newColor:
                    if c < 0 or c > 255:
                        print("Invalid color in color pallet line " + line)
                        continue
                
                colorPallet.add(newColor)
            except:
                print("Invalid color in color pallet line " + line)
                continue
    print("Color pallet loaded from file with ", len(colorPallet), " colors")
    return list(colorPallet)

def getColorDist(color1, color2):
    return abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2]) + abs(color1[3] - color2[3])


def setColorPallet(image, colorPallet):
    if len(colorPallet) > 128:
        print("Too many colors in color pallet")
        return image
    print("Setting color pallet using", len(colorPallet), "colors")

    # convert all colors to np.uint16
    for i in range(len(colorPallet)):
        colorPallet[i] = np.int16(colorPallet[i])
    numToDo = image.shape[0] * image.shape[1]
    numDown = 0
    lastPercentDone = 0
    timeAtStart = time.time()
    
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            closestColor = None
            closestDistance = 999999999
            for color in colorPallet:
                distance = getColorDist(image[y][x], color)
                if distance < closestDistance:
                    closestDistance = distance
                    closestColor = color
            image[y][x] = closestColor
            numDown += 1
            lastPercentDone = timeIt(numDown, numToDo, lastPercentDone, timeAtStart)
    print()
    return image
    

def upscale(image, xRatio, yRatio):
    print("Scaling image to correct ratios")
    # Create the new image
    newImage = np.zeros((image.shape[0] * yRatio, image.shape[1] * xRatio, image.shape[2]), np.uint8)
    numToDo = image.shape[0] * image.shape[1]
    numDown = 0
    lastPercentDone = 0
    timeAtStart = time.time()
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            for i in range(x * xRatio, (x + 1) * xRatio):
                for j in range(y * yRatio, (y + 1) * yRatio):
                    newImage[j][i] = image[y][x]
            numDown += 1
            lastPercentDone = timeIt(numDown, numToDo, lastPercentDone, timeAtStart)
    print()
    return newImage


def Pixelate(image, width, height, shouldUseImageColors=False):
    print("Pixelizing image")
    # Get the dimensions of the image
    imageHeight = image.shape[0]
    imageWidth = image.shape[1]
    imageChannels = image.shape[2]
    
    # Calculate the number of pixels in each direction
    pixelHeight = int(imageHeight / height)
    pixelWidth = int(imageWidth / width)
 
    xRatio = (int) (imageWidth / width)
    yRatio = (int) (imageHeight / height)
  
    # correct width and height so that we can have good averages
    width = (int) (imageWidth / xRatio)
    height = (int) (imageHeight / yRatio)
 
    # Create the new image
    newImage = np.zeros((height, width, imageChannels), np.uint8)

    numToDo = width * height
    numDown = 0
    lastPercentDone = 0
    timeAtStart = time.time()
    for x in range(width):
        for y in range(height):
            avg = np.zeros((imageChannels), np.uint32)
            numInAvg = 0
            colorsSet = set()
            for i in range(x * xRatio, (x + 1) * xRatio):
                for j in range(y * yRatio, (y + 1) * yRatio):
                    avg += image[j][i]
                    numInAvg += 1
                    if (shouldUseImageColors):
                        colorsSet.add(tuple(np.int32(image[j][i])))
            newImage[y][x] = avg / numInAvg
            if (shouldUseImageColors):
                # find which color the average is closest to and set it to that instead
                closestColor = None
                closestDistance = 999999999
                for color in colorsSet:
                    distance = getColorDist(newImage[y][x], color)
                    if distance < closestDistance:
                        closestDistance = distance
                        closestColor = color
                newImage[y][x] = closestColor
            numDown += 1
            lastPercentDone = timeIt(numDown, numToDo, lastPercentDone, timeAtStart)
    print()

    newImage = upscale(newImage, xRatio, yRatio)
    return newImage

def main():
    fileName = ""
    width = -1
    height = -1
    forceColors = "Correct"
    try:
        fileName = sys.argv[1]
        newRes = sys.argv[2] # formated as "WidthxHeight"
        newRes = newRes.replace(",", "x")
        width = int(newRes.split("x")[0])
        height = int(newRes.split("x")[1])
        if (len(sys.argv) > 3):
            forceColors = sys.argv[3]
    except:
        print("Usage:")
        print("python Pixelator.py <filename> <NewResXxNewResY>")
        print("python Pixelator.py <filename> <NewResXxNewResY> <ForceColors>")
        print("Force colors can be File,Correct,None")
        print("    File will take a color pallet from colorPallet.txt")
        print("    Correct will use the colors from the image")
        print("    None will just average the colors and not color correct")
        quit()
    
    # get the start time
    startTime = time.time()
        
    # Load the image
    originalImage = iio.imread(imageInputPath + fileName)

    hadAlpha = True
    # if theres no alpha value on the pixels, add one
    if (originalImage.shape[2] == 3):
        originalImage = np.dstack((originalImage, np.ones((originalImage.shape[0], originalImage.shape[1]), np.uint8) * 255))
        hadAlpha = False

    if (forceColors == "Correct"):
        newImage = Pixelate(originalImage, width, height, True)
    else:
        newImage = Pixelate(originalImage, width, height)
    
    colorPallet = []
    if (forceColors == "File"):
        colorPallet = getColorPalletForced()
    
    if (colorPallet != []):
        newImage = setColorPallet(newImage, colorPallet)
        
    if (hadAlpha == False):
        newImage = newImage[:,:,:3]
    # Save the image
    iio.imwrite(imageOutputPath + fileName, newImage)

    print("Total time taken:", round(time.time() - startTime,2), "seconds")


if __name__ == "__main__":
    main()