import sys

import numpy as np
import imageio as iio


imageInputPath = "images/"
imageOutputPath = "output/"


def getColorPallet(image):
    # make a set for the colors
    colorPallet = set()
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            colorPallet.add(tuple(image[y][x]))
    
  
    return colorPallet


def setColorPallet(image, colorPallet):
    if len(colorPallet) > 256:
        print("Too many colors in color pallet")
        return image
    print("Setting color pallet using", len(colorPallet), "colors")
    # go through each pixel and find the closest color in the pallet
    numToDo = image.shape[0] * image.shape[1]
    numDown = 0
    for x in range(image.shape[1]):
        for y in range(image.shape[0]):
            # copy the color pallet into a possible set
            possibleSet = set(colorPallet)

            for c in range(image.shape[2]):
                closestColor = None
                closestDistance = 999999999
                for color in colorPallet:
                    distance = np.linalg.norm(image[y][x] - color)
                    if distance < closestDistance:
                        closestDistance = distance
                        closestColor = color
            image[y][x] = closestColor
            numDown += 1
            if (numDown % 10 == 0):
                print(str(round((numDown / numToDo) * 100,2)) + "% done")
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



def main():
    fileName = ""
    width = -1
    height = -1
    try:
        fileName = sys.argv[1]
        newRes = sys.argv[2] # formated as "WidthxHeight"
        newRes = newRes.replace(",", "x")
        width = int(newRes.split("x")[0])
        height = int(newRes.split("x")[1])
    except:
        print("Usage: python Pixelator.py <filename> <NewResXxNewResY>")
        quit()
        
        
    print("File: " + imageInputPath + fileName)
    print("New Resolution: " + str(width) + "x" + str(height))
        
    # Load the image
    originalImage = iio.imread(imageInputPath + fileName)

    newImage = Pixelate(originalImage, width, height)
    colorPallet = getColorPallet(originalImage)
    setColorPallet(newImage, colorPallet)

    # Save the image
    iio.imwrite(imageOutputPath + fileName, newImage)



if __name__ == "__main__":
    main()