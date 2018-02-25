import sys, time
from queue import Queue
from time import sleep
import cv2
import os
import os.path

class Camera():

    def __init__(self):
        self.running_on_pi = os.getcwd().startswith('/home/pi')
        self.cam_fps = 10.0
        self.cam_width = 160
        self.cam_height = 120
        self.custom_shapes_names = ['triangle','heart', 'circle'] # 'star', 'square', 'cross']
        self.custom_shapes_contours = dict()
        self.cam_id = 0 if self.running_on_pi else 1 # 0 for default camera
        self.cam_buffer_threshold = 0.015 if self.running_on_pi else 0.00035
        self.frame_widths = [160,176,320,352,432,544,640,800,960,1184,1280]
        self.custom_shape_sim_threshold = 0.08
        
        self.look_back_window = 0
        self.previously_seen = Queue(maxsize=max(1, self.look_back_window))
        while not self.previously_seen.full():
            self.previously_seen.put('some strange unidentifiable shape')

        self.camera = self.setup_camera() 

    # Detects polygon with 3, 4, 5 or many sides in passed contour
    def detect_polygon(self, contour):
        shape = None
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

        if len(approx) == 3:
            return "triangle"
        elif len(approx) == 4:
            return "rectangle"
        elif len(approx) == 5:
            return "pentagon"
        else:
            return "circle"


    # Loads B&W binary images of custom shapes from the saved files
    # so we can then recognise the patterns in new images coming
    # from the camera
    def load_custom_shapes(self):
        for n in self.custom_shapes_names:
            img = cv2.imread(n + '.png')
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            self.custom_shapes_contours[n] = contours[0]


    # Detects any custom (loaded from files) shapes in passed contour
    def detect_custom_shape(self, contour_unknown):
        similarities = dict()
        
        for n, c_shape in self.custom_shapes_contours.items():
            sim = cv2.matchShapes(contour_unknown, c_shape, cv2.CONTOURS_MATCH_I1, 0.0)
            similarities[n] = sim

        sim_values = similarities.values()
        min_sim = min(sim_values)
        if min_sim > self.custom_shape_sim_threshold:
            return None
        else:
            for n, s in similarities.items():
                if s == min_sim:
                    return n


    # Returns a camera object with all important parameters set 
    # (resolution, FPS, contrast, B&W, etc)
    def setup_camera(self):
        camera = cv2.VideoCapture(self.cam_id)
            
        if not(camera.isOpened()):
            camera.open(self.cam_id)

        # Property codes from here:
        # https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture-set
        # REMEMBER to REMOVE the 'CV_' prefix
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_height)
        camera.set(cv2.CAP_PROP_FPS, self.cam_fps)
        camera.set(cv2.CAP_PROP_CONTRAST, 0.6)
        camera.set(cv2.CAP_PROP_SATURATION, 0.0)
        camera.set(cv2.CAP_PROP_GAIN, 0.0)
        return camera


    # Closes the camera and destroys any graphical windows that 
    # have been generated
    def destroy_camera(self):
        self.camera.release()
        cv2.destroyAllWindows()


    # Scans custom shapes using the camera and saves them into files. 
    # Does NOT overwrite existing files.
    def capture_custom_shapes(self):
        for n in self.custom_shapes_names:
            fname = n + '.png'
            if not os.path.isfile(fname): 
                wait_time = 3
                for i in range(wait_time):
                    print("Taking a shot of {} in {}...".format(n, wait_time - i))
                    sleep(1)

                # cam = self.setup_camera()
                r, img_raw = self.camera.read()
                cam.release()
                img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
                img = cv2.GaussianBlur(img, (5, 5), 0)
                (thresh, img) = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY_INV)
                
                cv2.imwrite(fname, img)


    # Displays simple live stream coming from the camera.
    def stream_from_camera(self):
        if self.running_on_pi:
            print("Can't stream from the camera on Raspberry Pi!")
            return

        while(self.camera.isOpened()):
            ret, frame = self.camera.read()
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break    


    # Decides which shapes are really present in the image stream.
    # Can do simple smoothing for higher reliability: Only consider
    # shape as present if it occured in last N images.
    def pick_shapes_present_in_stream(self, custom_shapes):
        if self.look_back_window < 1:
            return set(custom_shapes)

        if self.previously_seen.full():
            self.previously_seen.get()
        
        self.previously_seen.put(custom_shapes)
        
        previously_seen_list = list(self.previously_seen.queue)
        shapes_seen_consistently = set()
        for shape in self.custom_shapes_names:
            seen_consistently = True
            for shapes_set in previously_seen_list:
                if shape not in shapes_set:
                    seen_consistently = False
                    break
            if seen_consistently:
                shapes_seen_consistently.add(shape)

        return shapes_seen_consistently


    # Takes images from camera and throws away those coming from the buffer
    # until it hits a fresh image. How it does this: Uses empirical threshold
    # because it takes much longer to fetch image from the camera than it takes
    # to fetch it just from the buffer.
    def get_fresh_image_from_camera(self, timeToRun=1):
        total_start = time.time()
        time_to_fetch = 0
        img = None

        while time_to_fetch < self.cam_buffer_threshold and time.time() - total_start < timeToRun:
            start = time.time()
            r, img = self.camera.read()
            end = time.time()
            time_to_fetch = end - start

        return img


    # Returns the X position (absolute, as an int) of the given contour
    # in the image.
    def get_x_position_of_contour(self, contour):
        moments = cv2.moments(contour)
        x_coordinate = int(moments['m10']/moments['m00'])
        return x_coordinate


    # Processes the camera stream, looking for the specified shape. Can be restricted
    # to only run for a maximum of timeToRun seconds and then return None if the desired
    # shape was not detected.
    def stream_and_detect(self, wantedShape, showStream=False, continuousStream=False, timeToRun=1):
        start = time.time()
        runAgain = True
        x_coordinate = None

        # Processes the live stream, for every snapshot detecting the shapes.
        while runAgain:
            print("...waiting for {} to appear ({:.3f})...".format(wantedShape, time.time() - start))
            
            # Get fresh image from camera (and don't wait for it more than 1 second)
            img_raw = self.get_fresh_image_from_camera(timeToRun=1)

            # We managed to get an image; continue and process the contours present in it
            if img_raw is not None:
                img_labelled = img_raw

                # Pre-process the image
                img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
                img = cv2.GaussianBlur(img, (5, 5), 0)
                (thresh, img) = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY_INV)
                
                # Find all contours in the image
                img, contours, hierarchy = cv2.findContours(img, 
                    cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                # Loop through found contours and try detecting those 
                # that resemble custom shapes or polygons.
                for c in contours:            
                    # Detect and remember all detected shapes
                    custom_shape_label = self.detect_custom_shape(c)

                    if showStream:
                        # Draw the filled contours into the original image
                        ratio = 1
                        M = cv2.moments(c)
                        if M["m00"] != 0:
                            cX = int((M["m10"] / M["m00"]) * ratio)
                            cY = int((M["m01"] / M["m00"]) * ratio)
                            
                            img_labelled = cv2.drawContours(img_raw, [c], -1, (0, 255, 0), 1)
                            
                            if custom_shape_label:
                                img_labelled = cv2.putText(img_labelled, custom_shape_label, (cX, cY), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                    if custom_shape_label == wantedShape:
                        x_coordinate = self.get_x_position_of_contour(c)
                        runAgain = False
                        print("...{} found!...".format(wantedShape))
                        break
                
                if showStream:
                    # Show the captured image with added shape contours 
                    # and possibly shape labels as well
                    cv2.imshow("Image", img_labelled)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # See in command line what we've found (less resource-intensive 
                # alternative of showing the contours and labels in the original image)
                # shapes_really_present = pick_shapes_present_in_stream(custom_shapes)
                # print("                                         Shapes present: {}".format(shapes_really_present))

            if not continuousStream and time.time() - start > timeToRun:
                runAgain = False
                print("...timing out, {} not spotted :-(...".format(wantedShape))
            else:
                sleep(0.1)

        return x_coordinate



    # Simple showcase of what this class can do.
    def demo(self):
        self.capture_custom_shapes()
        self.load_custom_shapes()

        self.stream_from_camera()

        for i in range(10):
            x = self.stream_and_detect(wantedShape='heart', showStream=self.running_on_pi)
            print(x)

        self.destroy_camera()

cam = Camera()
cam.demo()