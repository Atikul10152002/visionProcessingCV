import cv2
import os
# import time
import hsv_val
import numpy as np

sliderEnabled = 0
useSavedValues = 1

loop = 0


class openCvPipeline:
    def __init__(self, video):
        self.video = video

        # * default color slider positions
        self.hueLowStart = 0
        self.hueHighStart = 255
        self.saturationLowStart = 0
        self.saturationHighStart = 255
        self.valueLowStart = 0
        self.valueHighStart = 255
        self.blurLow = 0

        if useSavedValues:
            self.hueLowStart = hsv_val.hueLow
            self.hueHighStart = hsv_val.hueHigh
            self.saturationLowStart = hsv_val.saturationLow
            self.saturationHighStart = hsv_val.saturationHigh
            self.valueLowStart = hsv_val.valueLow
            self.valueHighStart = hsv_val.valueHigh
            self.blurLow = hsv_val.blur

        # * Max values
        self.hsvMaxValue = 255
        self.blurMax = 100
        self.privCenter = None

        # * reduced frame rate to avoid lag issues of less powerful computers
        # framesPerSecond = 2 if sliderEnabled else self.video.get(cv2.CAP_PROP_FPS)
        self.framesPerSecond = 60

        # * slider names
        self.hh = 'Hue High'
        self.hl = 'Hue Low'
        self.sh = 'Saturation High'
        self.sl = 'Saturation Low'
        self.vh = 'Value High'
        self.vl = 'Value Low'
        self.br = 'Blur'
        self.wnd = 'Colorbars'
        self.kernelSize = 'kernel_size'
        self.kernelDivision = 'kernel_division'

        self.clicks = []
        self.maxLineCount = 10
        # * windows for sliders
        # ? namedWindow(winname[, flags]) -> None
        cv2.namedWindow(self.wnd, cv2.WINDOW_AUTOSIZE)
        # * create sliders
        # ? (bar name, window name, min , max, argument)
        if sliderEnabled:
            cv2.createTrackbar(self.hl, self.wnd, self.hueLowStart,
                               self.hsvMaxValue, self.nothing)
            cv2.createTrackbar(self.hh, self.wnd,
                               self.hueHighStart, self.hsvMaxValue, self.nothing)
            cv2.createTrackbar(self.sl, self.wnd,
                               self.saturationLowStart, self.hsvMaxValue, self.nothing)
            cv2.createTrackbar(self.sh, self.wnd,
                               self.saturationHighStart, self.hsvMaxValue, self.nothing)
            cv2.createTrackbar(self.vl, self.wnd,
                               self.valueLowStart, self.hsvMaxValue, self.nothing)
            cv2.createTrackbar(self.vh, self.wnd,
                               self.valueHighStart, self.hsvMaxValue, self.nothing)
            cv2.createTrackbar(self.br, self.wnd, self.blurLow,
                               self.blurMax, self.nothing)

        # * Testing with different values to denoise
        # cv2.createTrackbar(self.kernelSize, self.wnd, 1, 10, self.nothing)
        # cv2.createTrackbar(self.kernelDivision, self.wnd, 1, 25, self.nothing)

    def run(self):
        self.capture = self.video

        # * After 100 tries the program quits
        errors = 0
        frame_counter = 0
        pnts = []
        self.actualFPS = self.capture.get(cv2.CAP_PROP_FPS)

        print(f"source FPS: {self.actualFPS}")

        while(1):
            # while(self.capture.isOpened()):
            self.ret, self.frame = self.capture.read()
            if self.ret == True:
                # self.frame = cv2.rotate(
                    # self.frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                # * resizing the frame to better fit the screen
                self.frame = cv2.flip(self.frame, 1)
                self.frame = cv2.resize(self.frame,
                                        (int(self.frame.shape[1]//2),
                                         int(self.frame.shape[0]//2)))

                # * Returns hueLow, hueHigh, saturationLow, saturationHigh, valueLow, valueHigh, blur
                self.sliderValues = self.getSliderValues()

                # * Returns the masked image
                self.mask = self.getMask(
                    self.frame, *self.sliderValues)

                # * Returns the contour of the masked image
                self.contours = self.getContours(self.mask)

                # * draws circle on the contour
                self.center = self.findPart(self.contours)

                # TRAIL
                pnts.append(self.center)
                if len(pnts) > self.maxLineCount:
                    pnts.pop(0)
                for i in range(1, len(pnts)):
                    if pnts[i - 1] is None or pnts[i] is None:
                        continue
                    else:
                        if pnts[i] != (0, 0) and pnts[i-1] != (0, 0):
                            thickness = int(i) if int(i) != 0 else 1
                            cv2.line(self.frame, pnts[i - 1],
                                     pnts[i], (0, 0, 255), thickness)

                # VELOCITY
                self.velocityPix = self.findVelocity(self.center)
                cv2.putText(self.frame,  "."*round((self.velocityPix/self.actualFPS)*10),
                            (0, 10), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 255, 255), 10, cv2.LINE_AA)
                # print(f"center:", " " * ((10)-len(str(self.center))),
                #       self.center, " velocity: ", "*"*round((self.velocity/self.actualFPS)*80))

                # cv2.setMouseCallback(self.wnd, self.mouse_click)
                # if len(self.clicks) == 2:
                #     lineHeight = abs(self.clicks[0][1]-self.clicks[1][1])
                #     pixToInch = lineHeight/96
                #     self.velocity = (self.velocityPix*pixToInch)/self.actualFPS
                #     # print(f"velocity: {round(self.velocity, 5)} per inch")
                #     cv2.line(
                #         self.frame, self.clicks[0], (self.clicks[0][0], self.clicks[0][1]+lineHeight), (255,0,0), 1)

                # * showing contour and mask
                # ? imshow(winname, mat) -> None
                cv2.imshow('mask', self.mask)
                cv2.imshow(self.wnd, self.frame)

                # * defining frames per second
                if sliderEnabled:
                    key = cv2.waitKey(1)
                else:
                    key = cv2.waitKey(int(1000//self.framesPerSecond))

                # * save the slider values on the keypress of "s"
                if key == ord('s') and sliderEnabled:
                    self.writeHSV(*self.sliderValues)

                # * quit the program s on the keypress of "q"
                elif key == ord('q'):
                    self.capture.release()
                    break

                elif key == ord('c'):
                    self.clicks = []

                if loop:
                    frame_counter += 1
                    # If the last frame is reached, reset the capture and the frame_counter
                    if frame_counter == self.capture.get(cv2.CAP_PROP_FRAME_COUNT):
                        frame_counter = 0
                        self.privCenter = None
                        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                errors += 1
                if errors > 100:
                    self.capture.release()
                    break

    def nothing(self, *a, **k):
        '''
        empty function called by trackbars
        '''
        pass

    def writeHSV(self, hueLow, hueHigh, saturationLow, saturationHigh, valueLow, valueHigh, blur):
        '''
        writes calibrated hsv value of target to text file
        writeHSV(self) -> None
        '''

        # * Appending the final HSV values to the `file`
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'hsv_val.py'), 'a') as file:
            file.write('#'*10 + '\n')
            file.write('hueLow = ' + str(hueLow) + '\n')
            file.write('hueHigh = ' + str(hueHigh) + '\n')
            file.write('saturationLow = ' + str(saturationLow) + '\n')
            file.write('saturationHigh = ' + str(saturationHigh) + '\n')
            file.write('valueLow = ' + str(valueLow) + '\n')
            file.write('valueHigh = ' + str(valueHigh) + '\n')
            file.write('blur = ' + str(blur) + '\n')
            file.close()

    def getSliderValues(self):
        '''
        returns the slider values
        '''
        # * read trackbar positions for each trackbar. The function returns the current position of the specified trackbar
        # ? getTrackbarPos(trackbarname, winname) -> retval
        hueLow = cv2.getTrackbarPos(
            self.hl, self.wnd) if sliderEnabled else hsv_val.hueLow
        hueHigh = cv2.getTrackbarPos(
            self.hh, self.wnd) if sliderEnabled else hsv_val.hueHigh
        saturationLow = cv2.getTrackbarPos(
            self.sl, self.wnd) if sliderEnabled else hsv_val.saturationLow
        saturationHigh = cv2.getTrackbarPos(
            self.sh, self.wnd) if sliderEnabled else hsv_val.saturationHigh
        valueLow = cv2.getTrackbarPos(
            self.vl, self.wnd) if sliderEnabled else hsv_val.valueLow
        valueHigh = cv2.getTrackbarPos(
            self.vh, self.wnd) if sliderEnabled else hsv_val.valueHigh
        blur = (cv2.getTrackbarPos(self.br, self.wnd) if cv2.getTrackbarPos(
            self.br, self.wnd) % 2 != 0 else cv2.getTrackbarPos(
            self.br, self.wnd) + 1) if sliderEnabled else hsv_val.blur

        return hueLow, hueHigh, saturationLow, saturationHigh, valueLow, valueHigh, blur

    def findPart(self, contours):
        '''
        locates object and its centroid
        findPart(self, contours) -> None
        '''

        '''
        # quick and janky but your milege may vary
        (x, y), radius = cv2.minEnclosingCircle(contour)
        center = (int(x), int(y))
        radius = int(radius)
        cv2.circle(self.frame, center, radius, (0, 255, 0), 2)
        '''

        self.center = (0, 0)

        if len(contours) != 0:
            for contour in contours:
                # contour = max(contours, key=cv2.contourArea)
                # ? contourArea(contour[, oriented]) -> retval
                # * The function computes a contour area. Similarly to moments , the area is computed using the Green. formula. Thus, the returned area and the number of non-zero pixels, if you draw the contour using. \  # drawContours or \#fillPoly , can be different. Also, the function will most certainly give a wrong. results for contours with self-intersections
                self.A = cv2.contourArea(contour)

                # ? moments(array[, binaryImage]) -> retval
                # * The function computes moments, up to the 3rd order, of a vector shape or a rasterized shape. The results are returned in the structure cv: : Moments.
                # * Image Moment is a particular weighted average of image pixel intensities
                # * calculates moments of binary image
                self.M = cv2.moments(contour)
                # * Radius = sqrt(Area * Pi)
                self.Radius = int((self.A/3.14)**(.5))
                # ? change this value if target is smaller/larger
                if self.A > 1000:

                    # ? drawContours(image, contours, contourIdx, color[, thickness[, lineType[, hierarchy[, maxLevel[, offset]]]]]) -> image
                    cv2.drawContours(self.mask, [contour], -1, (0, 0, 255), 3)
                    # * uses the contour's 'moment' to find centroid
                    if self.M['m00'] != 0:
                        # * calculate x,y coordinate of center
                        self.circleX = int(self.M['m10']/self.M['m00'])
                        self.circleY = int(self.M['m01']/self.M['m00'])
                        self.center = (self.circleX, self.circleY)

                    # ? circle(img, center, radius, color[, thickness[, lineType[, shift]]]) -> img
                    # * The function cv::circle draws a simple or filled circle with a given center and radius

                    self.rect = cv2.minAreaRect(contour)
                    self.box = cv2.boxPoints(self.rect)
                    self.box = np.int0(self.box)
                    cv2.drawContours(self.frame, [self.box], 0, (0, 255, 0), 2)

                    # * Centroid center circle
                    cv2.circle(self.frame, self.center,
                               4, (0, 0, 255), -1)
                    # * Centroid surrounding circle
                    cv2.circle(self.frame, self.center,
                               self.Radius, (255, 0, 0), 1)

        return self.center

    def findVelocity(self, center):
        self.velocity = 0
        if self.privCenter == None:
            self.privCenter = self.center
        else:
            self.velocity = (
                ((((self.privCenter[0]-self.center[0])**2)+((self.privCenter[1]-self.center[1])**2)))**(.5))
            self.privCenter = self.center

        return self.velocity

    # @staticmethod
    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.clicks) <= 2:
                self.clicks.append((x, y))

    def getContours(self, mask):
        '''
        analyzes video feed and finds contours
        getContours(self, frame) -> contours
        '''
        # ? cvtColor(src, code[, dst[, dstCn]]) -> dst
        # * use greyscale (single channel) to remove blobs and draw contours
        # * The function converts an input image from one color space to another
        self.grey = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        # blob removal

        # * biggern kernel sizel will lead to more areas being ignored
        self.morphkernel = np.ones((1, 1), np.uint8)

        # self.dilatekernel = np.ones((5, 5), np.uint8)
        # self.kernel = np.ones((
        #     cv2.getTrackbarPos(self.kernelSize, self.wnd),
        #     cv2.getTrackbarPos(self.kernelSize, self.wnd)),
        #     np.uint8)/cv2.getTrackbarPos(self.kernelDivision, self.wnd)

        # self.eroded = cv2.erode(self.grey, self.kernel, iterations=1)
        # self.dialated = cv2.dilate(self.grey, self.kernel, iterations=1)

        # ? morphologyEx(src, op, kernel[, dst[, anchor[, iterations[, borderType[, borderValue]]]]]) -> dst

        self.morphed = cv2.morphologyEx(
            self.grey, cv2.MORPH_CLOSE, self.morphkernel)
        self.morphed = cv2.morphologyEx(
            self.morphed, cv2.MORPH_OPEN, self.morphkernel)

        # ? findContours(image, mode, method[, contours[, hierarchy[, offset]]]) -> image, contours, hierarchy
        # * The function retrieves contours from the binary image using the algorithm passed as an argument
        self.contours = cv2.findContours(
            self.morphed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2]
        return self.contours

    def getMask(self, frame, hueLow, hueHigh, saturationLow, saturationHigh, valueLow, valueHigh, blur):
        '''
        applies mask using hsv trackbar values
        getImage(self, frame) -> res
        '''

        # ? GaussianBlur(src, ksize, sigmaX[, dst[, sigmaY[, borderType]]]) -> dst
        frame = cv2.GaussianBlur(frame, (blur, blur), 0)

        # ? cvtColor(src, code[, dst[, dstCn]]) -> dst
        # * The function converts an input image from one color space to another
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # * define range of mask
        self.HSV_LOW = np.array([hueLow, saturationLow, valueLow])
        self.HSV_HIGH = np.array([hueHigh, saturationHigh, valueHigh])

        # * create a mask with the hsv range
        mask = cv2.inRange(hsv, self.HSV_LOW, self.HSV_HIGH)
        # * cancel out everyting that doesn't belong to the mask
        # * computes bitwise conjunction of the two arrays (dst = src1 & src2)
        mask = cv2.bitwise_and(frame, frame, mask=mask)
        return mask


# * captures the videofeed from camera
# * Try (0) or (1)
source = cv2.VideoCapture(0)

# filePath = "VID_20180921_180711.mp4"
# source = cv2.VideoCapture(
#     os.path.join(os.path.abspath(os.path.dirname(__file__)), filePath))


cv = openCvPipeline(source)
cv.run()

# * release everything at the end of the operation
source.release()
cv2.destroyAllWindows()
