import sys, time
from queue import Queue
from time import sleep
from multiprocessing import Process, Manager
import cv2
import os, os.path

class Camera():

    def __init__(self):
        self.running_on_pi = os.getcwd().startswith('/home/pi')
        self.running_on_dice = os.getcwd().startswith('/afs/inf.ed.ac.uk')
        self.cam_fps = 10.0
        self.cam_width = 160
        self.cam_height = 120
        self.custom_shapes_names = ['triangle', 'heart', 'circle', 'star'] #, 'square', 'cross']
        self.custom_shapes_contours = dict()
        self.cam_id = 0 if self.running_on_pi or self.running_on_dice else 1 # 0 for default camera
        if self.running_on_pi:
            self.cam_buffer_threshold = 0.5 # 0.015
        else:
            self.cam_buffer_threshold = 0.00035
        self.frame_widths = [160,176,320,352,432,544,640,800,960,1184,1280]
        self.custom_shape_sim_threshold = 0.08

        self.look_back_window = 0
        self.previously_seen = Queue(maxsize=max(1, self.look_back_window))
        while not self.previously_seen.full():
            self.previously_seen.put('some strange unidentifiable shape')

        self.setup_camera()

        self.multi_thread_dict = dict()


    def setup_multithreading(self):
        if self.multi_thread_dict is None:
            self.multi_thread_dict = Manager().dict()


    def check_camera(self):
        while not self.camera:
            print("Camera not found, setting it up")
            self.setup_camera()

        while not self.camera.isOpened():
            print("Camera not opened, opening it up")
            self.camera.open(self.cam_id)

        print("{}x{}".format(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)))

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
            # path = os.getcwd() + '/vision'
            img = cv2.imread('vision/' + n + '.png')
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            self.custom_shapes_contours[n] = contours[0]


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


    # Returns a camera object with all important parameters set 
    # (resolution, FPS, contrast, B&W, etc)
    def setup_camera(self):
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


    # Closes the camera and destroys any graphical windows that 
    # have been generated
    def destroy_camera(self):
        # time.sleep(0.3)
        self.camera.release()
        # time.sleep(0.3)

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
    def get_fresh_image_from_camera(self, timeToRun=1.0, multiThread=True):
        self.check_camera()

        total_start = time.time()
        time_to_fetch = 0
        self.multi_thread_dict['img'] = None
        
        if multiThread:
            r, i = self.camera.read()

        while time_to_fetch < self.cam_buffer_threshold and time.time() - total_start < timeToRun:
            start = time.time()
            img = None
            self.multi_thread_dict['img'] = None
            
            if multiThread:
                cam_process = Process(target=self.read_from_camera, name="CamProcess", args=(self.multi_thread_dict, 0))
                cam_process.start()
                cam_process.join(timeToRun)
                if cam_process.is_alive():
                    cam_process.terminate()
            else:
                self.read_from_camera(self.multi_thread_dict)

            time_to_fetch = time.time() - start
            print("        ({:.4f})".format(time_to_fetch))

        return self.multi_thread_dict['img']
    

    def read_from_camera(self, return_dict, random_arg=0):
        _, img = self.camera.read()
        return_dict['img'] = img


    # Returns the X position (absolute, as an int) of the given contour
    # in the image.
    def get_x_position_of_contour(self, contour):
        moments = cv2.moments(contour)
        x_coordinate = int(moments['m10']/moments['m00'])
        return x_coordinate


    def get_contours(self, img):
        # Pre-process the image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.GaussianBlur(img, (5, 5), 0)
        (thresh, img) = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY_INV)
        
        # Find all contours in the image
        img, contours, hierarchy = cv2.findContours(img, 
            cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        return contours, img


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


    # Processes the camera stream, looking for the specified shape. Can be restricted
    # to only run for a maximum of timeToRun seconds and then return None if the desired
    # shape was not detected.
    def stream_and_detect(self, wantedShape, showStream=False, continuousStream=False, timeToRun=1.0, multiThread=True):
        start = time.time()
        runAgain = True
        x_coordinate = None
        height = None

        if multiThread:
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


                if showStream:
                    img = self.draw_contour(img, best_contour, wantedShape)
                    # Show the captured image with added shape contours 
                    # and possibly shape labels as well
                    print("Height: {}px".format(self.get_contour_height(best_contour)))
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
        img = self.get_fresh_image_from_camera(timeToRun=2.0, multiThread=False)
        # print("image: {}found".format("not" if img is None else ""))
        if img is not None:
            contours, _ = self.get_contours(img)
            # print("{} contours".format(len(contours)))
            contour, label = self.find_most_salient_contour(contours)
            # print(contour, label)
            height = self.get_contour_height(contour)
            return label, height
        else:
            return None, None


    def get_contour_height(self, contour):
        x, y, w, h = cv2.boundingRect(contour)
        return h


    # Simple showcase of what this class can do.
    def demo(self):
        self.capture_custom_shapes()
        self.load_custom_shapes()

        shape = 'heart'

        # self.stream_from_camera()

        for i in range(1000):
            x, _ = self.stream_and_detect(wantedShape=shape, showStream=True, continuousStream=False, multiThread=False)
            
            if x:
                print("Position of {}: {}px.".format(shape, x))
            else:
                print(":-(")

        self.destroy_camera()

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

if __name__ == "__main__":
    cam = Camera()
    cam.load_custom_shapes()

    # cam.get_desired_shape()

    cam.demo()

    # cam.stream_from_camera()

    # shape = None
    # while shape is None:
    #     shape = cam.read_shape_from_card()
    # print(shape)
    
    # cam.read_shapes_for_confmtrx(30)