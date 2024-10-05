import sys

import numpy as np
import imageio.v2 as iio


imageInputPath = "images/"
imageOutputPath = "output/"

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


def getColorPalletOfImage(image, maxColors, whiteThreshold = 240):
    # go through the image and make all colors over whiteThreadhold white
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            for i in range(3):
                if (image[y][x][i] > whiteThreshold):
                    image[y][x][i] = 255
    
    # make a dict for the colors with how many times they appear
    colorPallet = {}
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            colorPallet[tuple(image[y][x])] = colorPallet.get(tuple(image[y][x]), 0) + 1

    colorPalletFinal = []
    # take the top maxColors colors
    for color in sorted(colorPallet, key=colorPallet.get, reverse=True):
        colorPalletFinal.append(color)
        if (len(colorPalletFinal) >= maxColors):
            break
    
    # only take the colors seen over 50 times
    # for color in colorPallet:
    #     if (colorPallet[color] > 50):
    #         colorPalletFinal.append(color)
    
    for color in colorPalletFinal:
        print(color)
    print("Color pallet loaded from image with", len(colorPalletFinal), "colors")
  
    return colorPalletFinal


def getColorDist(color1, color2):
    return abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2]) + abs(color1[3] - color2[3])

def crunchColorPallet(colorPallet, maxColors):
    newColorPallet = []
    smallestDists = []
    todo = len(colorPallet) * len(colorPallet)
    done = 0
    print("Crunching color pallet of" , len(colorPallet) ,"to", maxColors, "colors")

    numBefore = len(colorPallet)
    
    while  len(colorPallet) > maxColors:
        if (len(colorPallet) % 10 == 0):
            print("Color pallet down to", len(colorPallet), "colors")
        for i in range(len(colorPallet)):
            colorPallet[i] = np.int32(colorPallet[i])
        dictOfColorsToAverageDiff = {}
        lowestDiffColorIndex = None
        lowestDiff = 999999999
        # get the average diff of each color compared to other colors
        for i in range(len(colorPallet)):
            color = colorPallet[i]
            avgDiff = 0
            for color2 in colorPallet:
                avgDiff += getColorDist(color, color2)
            avgDiff /= len(colorPallet)
            dictOfColorsToAverageDiff[tuple(color)] = avgDiff
            if (avgDiff < lowestDiff):
                lowestDiff = avgDiff
                lowestDiffColorIndex = i
        
        # remove the lowest diff from the color pallet
        colorPallet.pop(lowestDiffColorIndex)
    
    print("Color pallet Was", numBefore, "colors, and is now", len(colorPallet), "colors")             
    
    return list(colorPallet)

def setColorPallet(image, colorPallet, maxColors):
    if maxColors > 512:
        print("Too many colors in color pallet")
        return image
    print("Setting color pallet using", maxColors, "colors")
    # go through each pixel and find the closest color in the pallet
    if (len(colorPallet) > maxColors):
        colorPallet = crunchColorPallet(colorPallet, maxColors)
    
    # convert all colors to np.uint16
    for i in range(len(colorPallet)):
        colorPallet[i] = np.int16(colorPallet[i])
    numToDo = image.shape[0] * image.shape[1]
    numDown = 0
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
            # round to the nearest 2 decimal
            percentDone = numDown / numToDo * 100
            if (percentDone % 1 == 0):
                print(str(percentDone) + "% done")
    return image


def roundColors(image, roundTo):
    # round each color to the nearest roundTo
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            for i in range(3):
                image[y][x][i] = int(image[y][x][i] / roundTo) * roundTo
    
    return image
    

def upscale(image, xRatio, yRatio):
    # Create the new image
    newImage = np.zeros((image.shape[0] * yRatio, image.shape[1] * xRatio, image.shape[2]), np.uint8)
 
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            for i in range(x * xRatio, (x + 1) * xRatio):
                for j in range(y * yRatio, (y + 1) * yRatio):
                    newImage[j][i] = image[y][x]
    
    return newImage


def Pixelate(image, width, height):
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

    for x in range(width):
        for y in range(height):
            avg = np.zeros((imageChannels), np.uint32)
            numInAvg = 0
            for i in range(x * xRatio, (x + 1) * xRatio):
                for j in range(y * yRatio, (y + 1) * yRatio):
                    avg += image[j][i]
                    numInAvg += 1
            newImage[y][x] = avg / numInAvg

    newImage = upscale(newImage, xRatio, yRatio)
    
    return newImage


def numColors(image):
    colorSet = set()
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            colorSet.add(tuple(image[y][x]))
    return len(colorSet)


def main():
    fileName = ""
    width = -1
    height = -1
    forceColors = "None"
    maxColors = 20
    whiteThreshold = 240
    try:
        fileName = sys.argv[1]
        newRes = sys.argv[2] # formated as "WidthxHeight"
        newRes = newRes.replace(",", "x")
        width = int(newRes.split("x")[0])
        height = int(newRes.split("x")[1])
        if (len(sys.argv) > 3):
            forceColors = sys.argv[3]
        if (len(sys.argv) > 4):
            maxColors = int(sys.argv[4])
        if (len(sys.argv) > 5):
            whiteThreshold = int(sys.argv[5])
    except:
        print("Usage:")
        print("python Pixelator.py <filename> <NewResXxNewResY>")
        print("python Pixelator.py <filename> <NewResXxNewResY> <ForceColors>")
        print("python Pixelator.py <filename> <NewResXxNewResY> <ForceColors> <MaxColors||roundTo> <whiteThreshold>")
        print("Force colors can be File,TakeFromImage,Round,None")
        quit()
        
        
    # Load the image
    originalImage = iio.imread(imageInputPath + fileName)

    hadAlpha = True
    # if theres no alpha value on the pixels, add one
    if (originalImage.shape[2] == 3):
        originalImage = np.dstack((originalImage, np.ones((originalImage.shape[0], originalImage.shape[1]), np.uint8) * 255))
        hadAlpha = False

    newImage = Pixelate(originalImage, width, height)
    
    colorPallet = []
    if (forceColors == "File"):
        colorPallet = getColorPalletForced()
    elif (forceColors == "TakeFromImage"):
        colorPallet = getColorPalletOfImage(originalImage, maxColors, whiteThreshold)
    
    if (colorPallet != []):
        newImage = setColorPallet(newImage, colorPallet, maxColors)
    elif (forceColors == "Round"):
        newImage = roundColors(newImage, maxColors)
        
        
    if (hadAlpha == False):
        newImage = newImage[:,:,:3]
    # Save the image
    iio.imwrite(imageOutputPath + fileName, newImage)


if __name__ == "__main__":
    main()