import cv2
# import time
import numpy as np
import hsv_val

sliderEnabled = 0


class openCvPipeline:
    # * default color slider positions
    hueLowStart = 0
    hueHighStart = 255
    saturationLowStart = 0
    saturationHighStart = 255
    valueLowStart = 0
    valueHighStart = 255
    blurLow = 0
    # * Max values
    hsvMaxValue = 255
    blurMax = 100
    privCenter = None

    # * reduced frame rate to avoid lag issues of less powerful computers
    # framesPerSecond = 2 if sliderEnabled else 1
    framesPerSecond = 60

    # * slider names
    hh = 'Hue High'
    hl = 'Hue Low'
    sh = 'Saturation High'
    sl = 'Saturation Low'
    vh = 'Value High'
    vl = 'Value Low'
    br = 'Blur'
    wnd = 'Colorbars'
    kernelSize = 'kernel_size'
    kernelDivision = 'kernel_division'
    centers = []

    def __init__(self):
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

    def run(self, video):
        self.capture = video

        # * After 100 tries the program quits
        errors = 0
        frame_counter = 0
        firstRun = True
        fullRunCenters = None
        privCenter = None

        while(True):
            # while(self.capture.isOpened()):
            self.ret, self.frame = self.capture.read()
            if self.ret == True:
                self.frame = cv2.rotate(
                    self.frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                # * resizing the frame to better fit the screen
                self.frame = cv2.resize(self.frame,
                                        (int(self.frame.shape[1]/4),
                                         int(self.frame.shape[0]/4)))

                # * Returns hueLow, hueHigh, saturationLow, saturationHigh, valueLow, valueHigh, blur
                self.sliderValues = self.getSliderValues()

                # * Returns the masked image
                self.mask = self.getMask(
                    self.frame, *self.sliderValues)

                # * Returns the contour of the masked image
                self.contours = self.getContours(self.mask)

                # * draws circle on the contour
                self.center = self.findPart(self.contours)
                self.centers.append(self.center)
                for acenter in self.centers:
                    if self.privCenter is not None:
                        cv2.line(
                            self.mask, acenter, self.privCenter, (255, 0, 0), 1)
                        self.privCenter = acenter
                    else:
                        self.privCenter = acenter

                self.velocity = self.findVelocity(self.center)
                cv2.putText(self.mask,  "."*round(self.velocity*120),
                    (0, 15), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 10, cv2.LINE_AA)
                # print(f"center:", " " * ((10)-len(str(self.center))),
                #       self.center, " velocity: ", "*"*round(self.velocity*80))


                # * showing contour and mask
                # ? imshow(winname, mat) -> None
                cv2.imshow('mask', self.mask)
                cv2.imshow(self.wnd, self.frame)

                # * defining frames per second
                key = cv2.waitKey(1000//self.framesPerSecond)

                # * save the slider values on the keypress of "s"
                if key == ord('s') and sliderEnabled:
                    self.writeHSV(*self.sliderValues)

                # * quit the program s on the keypress of "q"
                if key == ord('q'):
                    self.capture.release()
                    break

                frame_counter += 1
                # If the last frame is reached, reset the capture and the frame_counter
                if frame_counter == self.capture.get(cv2.CAP_PROP_FRAME_COUNT):
                    frame_counter = 0
                    if firstRun:
                        firstRun = False
                        fullRunCenters = self.centers
                    self.centers = fullRunCenters
                    self.privCenter = None
                    print(len(fullRunCenters))
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                errors += 1
                if errors > 100:
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
        with open('hsv_val.py', 'a') as file:
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
            contour = max(contours, key=cv2.contourArea)
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
                cv2.circle(self.mask, self.center,
                           4, (159, 159, 255), -1)
                # * Centroid surrounding circle
                cv2.circle(self.mask, self.center,
                           self.Radius, (255, 0, 0), 1)

        return self.center

    def findVelocity(self, center):
        self.velocity = 0
        if self.privCenter == None:
            self.privCenter = self.center
        else:
            self.velocity = (
                ((((self.privCenter[0]-self.center[0])**2)+((self.privCenter[1]-self.center[1])**2)))**(.5))/60
            self.privCenter = self.center

        return self.velocity

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


cv = openCvPipeline()

# * captures the videofeed from camera
# * Try (0) for Windows and Linux and (1) for Mac
camera = cv2.VideoCapture("/Users/atikul/Downloads/VID_20180921_180711.mp4")
# camera = cv2.VideoCapture()  # * Try (0) for Windows and Linux and (1) for Mac
# time.sleep(2)

cv.run(camera)

# * release everything at the end of the operation
camera.release()
cv2.destroyAllWindows()
