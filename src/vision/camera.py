import sys, time
from queue import Queue
from time import sleep
from multiprocessing import Process, Manager
import cv2
import os, os.path
sys.path.insert(0, os.getcwd())
# import Software.pour_it_utils

from picamera.array import PiRGBArray
from picamera import PiCamera

class Camera():
    ###########################################################################
    # SETTING UP AND BASIC LOW-LEVEL OPERATION OF CAMERAS
    ###########################################################################

    def __init__(self):
        self.images_path = '' if os.getcwd().endswith('/vision') else 'vision/'
        self.running_on_pi = os.getcwd().startswith('/home/pi')
        self.running_on_dice = os.getcwd().startswith('/afs/inf.ed.ac.uk')
        self.using_picamera = self.running_on_pi
        
        self.cam_fps = 20.0
        self.custom_shapes_names = ['triangle', 'heart', 'circle', 'star'] #, 'square', 'cross']
        self.custom_shapes_contours = dict()
        self.custom_shape_sim_threshold = 0.08
        
        if not self.using_picamera:
            self.set_logitech_variables()

        self.look_back_window = 0
        self.previously_seen = Queue(maxsize=max(1, self.look_back_window))
        while not self.previously_seen.full():
            self.previously_seen.put('some strange unidentifiable shape')

        self.multi_thread_dict = dict()

        self.setup_camera()


    # Initialises parameters needed for using the Logitech camera, such
    # as the time thresholds needed for getting fresh images from the
    # buffer.
    def set_logitech_variables(self):
        self.cam_id = 0 if self.running_on_pi or self.running_on_dice else 1
        if self.running_on_pi:
            self.cam_buffer_threshold = 0.5 # 0.015
        else:
            self.cam_buffer_threshold = 0.00035
        self.frame_widths = [160,176,320,352,432,544,640,800,960,1184,1280]

    
    # Only for the Logitech camera if we want multithreading
    # for time-limited fresh image retrieving functionality 
    # (note that it's been working fine without this multithreading 
    # on Pi 3).
    def setup_multithreading(self):
        if self.using_picamera:
            print("WARNING: Cannot use multithreading with Pi camera!")
        else:
            if self.multi_thread_dict is None:
                self.multi_thread_dict = Manager().dict()


    # Returns a camera object with all important parameters set 
    # (resolution, FPS, contrast, B&W, etc)
    def setup_camera(self):
        if self.using_picamera:
            self.cam_width = 600
            self.cam_height = 200
            self.camera = PiCamera()
            self.camera.color_effects = (128, 128) #B&w mode
            self.camera.contrast = 70
            self.camera.framerate = self.cam_fps
            self.camera.resolution = (self.cam_width, self.cam_height)
            self.camera.zoom = (0.15, 0.15, 0.7, 0.7)
            self.cam_raw_capture = PiRGBArray(self.camera)
            
            print("Cam resolution: {}x{}".format(self.camera.resolution[0], self.camera.resolution[1]))

            # allow the camera to warmup
            time.sleep(1)
        else:
            self.cam_width = 160
            self.cam_height = 120
            self.camera = cv2.VideoCapture(self.cam_id)
            
            self.check_camera()

            # Property codes from here:
            # https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture-set
            # REMEMBER to REMOVE the 'CV_' prefix
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.cam_fps)
            self.camera.set(cv2.CAP_PROP_CONTRAST, 0.7)
            self.camera.set(cv2.CAP_PROP_SATURATION, 0.0)
            self.camera.set(cv2.CAP_PROP_GAIN, 0.0)


    # Makes sure that camera is running and ready. 
    # If not, tries to start the camera until everything is OK.
    def check_camera(self):
        camera_reset = False
        
        while not self.camera:
            print("Camera not found, setting it up")
            camera_reset = True
            self.setup_camera()

        cam_open = True if self.using_picamera else self.camera.isOpened()
        while not cam_open:
            print("Camera not opened, opening it up")
            if self.using_picamera:
                self.camera = PiCamera()
                sleep(0.1)
            else:
                self.camera.open(self.cam_id)
            cam_open = True if self.using_picamera else self.camera.isOpened()

        if camera_reset:
            if self.using_picamera:
                print("Cam resolution: {}x{}".format(self.camera.resolution[0], self.camera.resolution[1]))
            else:
                print("Cam resolution: {}x{}".format(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)))


    # Closes the camera and destroys any graphical windows that 
    # have been generated
    def destroy_camera(self):
        if self.using_picamera:
            self.camera.close()
            self.cam_raw_capture.truncate(0)
        else:
            self.camera.release()

        cv2.destroyAllWindows()


    # Lowest-level capturing of an image from any camera.
    def cam_read(self):
        if self.using_picamera:
            self.camera.capture(self.cam_raw_capture, format="bgr")
            image = self.cam_raw_capture.array
            self.cam_raw_capture.truncate(0)
            return None, image
        else:
            r, image = self.camera.read()
            return r, image


    # Basic low-level reading used with the Logitech camera (developed 
    # primarily for multithreading scenarios)
    def read_from_logitech_camera(self, return_dict, random_arg=0):
        if self.using_picamera:
            print("ERROR: Cannot use this method with Pi camera!")
        else:
            _, img = self.camera.read()
            return_dict['img'] = img


    # Takes images from camera and throws away those coming from the buffer
    # until it hits a fresh image. How it does this: Uses empirical threshold
    # because it takes much longer to fetch image from the camera than it takes
    # to fetch it just from the buffer.
    def get_fresh_image_from_camera(self, timeToRun=1.0, multiThread=False):
        self.check_camera()

        if self.using_picamera:
            _, image = self.cam_read()
            return image
        else:
            total_start = time.time()
            time_to_fetch = 0
            self.multi_thread_dict['img'] = None
            
            if multiThread:
                r, i = self.camera.read()

            while time_to_fetch < self.cam_buffer_threshold and time.time() - \
                total_start < timeToRun:
                start = time.time()
                img = None
                self.multi_thread_dict['img'] = None
                
                if multiThread:
                    cam_process = Process(target=self.read_from_logitech_camera, 
                        name="CamProcess", args=(self.multi_thread_dict, 0))
                    cam_process.start()
                    cam_process.join(timeToRun)
                    if cam_process.is_alive():
                        cam_process.terminate()
                else:
                    self.read_from_logitech_camera(self.multi_thread_dict)

                time_to_fetch = time.time() - start
                print("        ({:.4f})".format(time_to_fetch))

            return self.multi_thread_dict['img']
    
    
    ###########################################################################
    # WORKING WITH (PRE)DEFINED SHAPES
    ###########################################################################

    # Scans custom shapes using the camera and saves them into files. 
    # Does NOT overwrite existing files.
    def capture_custom_shapes(self):
        for n in self.custom_shapes_names:
            fname = self.images_path + n + '.png'
            if not os.path.isfile(fname): 
                wait_time = 3
                for i in range(wait_time):
                    print("Taking a shot of {} in {}...".format(n, wait_time - i))
                    sleep(1)

                r, img_raw = self.cam_read()
                image = self.apply_filters(img_raw)
                cv2.imwrite(fname, image)


    # Loads B&W binary images of custom shapes from the saved files
    # so we can then recognise the patterns in new images coming
    # from the camera
    def load_custom_shapes(self):
        for n in self.custom_shapes_names:
            img = cv2.imread(self.images_path + n + '.png')
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            self.custom_shapes_contours[n] = contours[0]


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


    # Detects any custom (loaded from files) shapes in passed contour
    def detect_custom_shape(self, contour_unknown):
        similarities = dict()

        for n, c_shape in self.custom_shapes_contours.items():
            sim = cv2.matchShapes(contour_unknown, c_shape, cv2.CONTOURS_MATCH_I1, 0.0)
            similarities[n] = sim

        sim_values = similarities.values() if len(similarities) > 0 else [10000]
        min_sim = min(sim_values)
        if min_sim > self.custom_shape_sim_threshold:
            return -10000, None
        else:
            for n, s in similarities.items():
                if s == min_sim:
                    return s*-1, n
   

    ###########################################################################
    # IMAGE PRE-PROCESSING, FINDING CONTOURS (SHAPES) AND THEIR PARAMETERS
    ###########################################################################

    # Blurs and binarises passed image.
    def apply_filters(self, image):
        if image is None:
            print("No image provided!")
            return None
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image = cv2.GaussianBlur(image, (5, 5), 0)
            (thresh, image) = cv2.threshold(image, 60, 255, cv2.THRESH_BINARY_INV)

            return image


    # Detects all contours in the given image.
    def get_contours(self, img):
        # Pre-process the image
        img = self.apply_filters(img)
        
        # Find all contours in the image
        img, contours, hierarchy = cv2.findContours(img, 
            cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        return contours, img


    # Finds the most salient contour or possibly the most salient exemplar
    # of a desired shape in the image.
    def find_most_salient_contour(self, contours, wantedShape=None):
        # Loop through found contours and try detecting those 
        # that resemble custom shapes or polygons.
        max_weight = -10000
        best_contour = None
        label_to_return = None

        for c in contours:         
            # Detect and remember all detected shapes
            weight, label = self.detect_custom_shape(c)            

            if weight > max_weight and (wantedShape is None or label == wantedShape):
                max_weight = weight
                best_contour = c
                label_to_return = label

        return best_contour, label_to_return


    # Returns the X position (absolute, as an int) of the given contour
    # in the image.
    def get_x_position_of_contour(self, contour):
        moments = cv2.moments(contour)
        x_coordinate = int(moments['m10']/moments['m00'])
        return x_coordinate


    # Height of given contour in pixels
    def get_contour_height(self, contour):
        x, y, w, h = cv2.boundingRect(contour)
        return h


    # Marks and labels the given contour in the image.
    def draw_contour(self, img, contour, label=None):
        if contour is None:
            return img

        # Draw the filled contours into the original image
        ratio = 1
        M = cv2.moments(contour)
        
        if M["m00"] != 0:
            cX = int((M["m10"] / M["m00"]) * ratio)
            cY = int((M["m01"] / M["m00"]) * ratio)
            
            img = cv2.drawContours(img, [contour], -1, (0, 255, 0), 1)
            
            if label:
                img = cv2.putText(img, label, (cX, cY), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return img


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


    # Displays simple live stream coming from the camera (only on non-Pi devices)
    def stream_from_camera(self):
        if self.using_picamera or self.running_on_pi:
            print("Can't stream when running on Raspberry Pi!")
            return
        else:
            while(self.camera.isOpened()):
                ret, frame = self.camera.read()
                cv2.imshow('frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break    


    # Processes the camera stream, looking for the specified shape. Can be restricted
    # to only run for a maximum of timeToRun seconds and then return None if the desired
    # shape was not detected.
    def stream_and_detect(self, wantedShape, showStream=False, continuousStream=False, timeToRun=1.0, saveImages=False, fname="img", multiThread=False):
        start = time.time()
        runAgain = True
        x_coordinate = None
        height = None

        if multiThread:
            if self.using_picamera:
                print("WARNING: Multithreading not supported with Pi camera.")
            else:
                self.setup_multithreading()

        # Processes the live stream, for every snapshot detecting the shapes.
        while runAgain:
            x_coordinate = None

            print("...waiting for {} ({:.3f})...".format(wantedShape, time.time() - start))
            
            # Get fresh image from camera (and don't wait for it more than 1 second)
            img = self.get_fresh_image_from_camera(timeToRun=2.0, multiThread=multiThread)

            # We managed to get an image; continue and process the contours present in it
            if img is not None:
                contours, img = self.get_contours(img)
                best_contour, _ = self.find_most_salient_contour(contours, wantedShape)
                
                if best_contour is not None:
                    x_coordinate = self.get_x_position_of_contour(best_contour)
                    height = self.get_contour_height(best_contour)
                    print("Height of best contour: {}px".format(self.get_contour_height(best_contour)))
                    
                    if saveImages:
                        img = self.draw_contour(img, best_contour, wantedShape)
                        cv2.imwrite(fname + ".jpg", img)


                if showStream:
                    if self.running_on_pi:
                        print("WARNING: Cannot show stream from camera on Raspberry Pi!")
                    else:
                        # Show the captured image with added shape contours 
                        # and possibly shape labels as well
                        img = self.draw_contour(img, best_contour, wantedShape)
                        cv2.imshow("Image", img)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                if best_contour is not None and not continuousStream:
                    return x_coordinate, height

            run_time = time.time() - start
            if not continuousStream and run_time > timeToRun:
                runAgain = False
                print("...timing out ({:.3f}), {} not spotted :-(...".format(run_time, wantedShape))
            else:
                pass

        return x_coordinate, height


    def read_shape_from_card(self):
        img = self.get_fresh_image_from_camera(timeToRun=2.0)
        if img is not None:
            contours, _ = self.get_contours(img)
            contour, label = self.find_most_salient_contour(contours)
            height = self.get_contour_height(contour)
            return label, height
        else:
            return None, None


    def read_shapes_for_confmtrx(self, distance):
        with open("shapes_" + str(distance) + "cm.txt", "w") as f:
            for i in range(3):
                for name in self.custom_shapes_names:
                    print("scanning {} in {}".format(name, 3))
                    sleep(1)
                    print("scanning {} in {}".format(name, 2))
                    sleep(1)
                    print("scanning {} in {}".format(name, 1))
                    sleep(1)
                    shapeCounter = 0
                    shape = None
                    while shapeCounter < 5:
                        shape = cam.read_shape_from_card()
                        if shape is not None:
                            shapeCounter += 1
                    f.write(name + "," + shape + "\n")


    def get_desired_shape(self, offset=6):
        shape = None
        i = 0
        while shape is None:
            print("waiting for shape")
            # discard first 5 reads that are not none (e.g a shape)
            shape, height = self.read_shape_from_card()
            if height < 10:
                shape = None
                continue

            if (shape is not None) and i < offset:
                print("found shape: " + shape)
                shape = None
                i += 1
            print(shape)

        return shape

    def contour_detection_demo(self, fname="img"):
        sleep(1)
        img = self.get_fresh_image_from_camera()
        img = self.apply_filters(img)
        contours, _ = self.get_contours(img)
        for contour in contours:
            img = self.draw_contour(img, contour)
        cv2.imwrite(fname + ".jpg", img)


    # Simple showcase of what this class can do.
    def demo(self):
        self.capture_custom_shapes()
        self.load_custom_shapes()

        shape = 'heart'

        if not self.using_picamera:
            self.stream_from_camera()

        for i in range(1000):
            fname = "img" + str(i)
            x, _ = self.stream_and_detect(wantedShape=shape, showStream=False, continuousStream=False, saveImages=True, fname=fname)
            
            if x:
                print("Position of {}: {}px.".format(shape, x))
            else:
                print(":-(")

        self.destroy_camera()

if __name__ == "__main__":
    cam = Camera()
    # cam.load_custom_shapes()

    # cam.get_desired_shape()
    # for i in range(10):
    #     cam.contour_detection_demo(str(i))

    cam.demo()

    # cam.stream_from_camera()

    # shape = None
    # while shape is None:
    #     shape = cam.read_shape_from_card()
    # print(shape)
    
    # cam.read_shapes_for_confmtrx(30)