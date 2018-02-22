import sys, time
from queue import Queue
from time import sleep
import numpy as np
import cv2
import os.path

#remote python call setup
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3']      #import ev3dev.ev3

custom_shapes_names = ['triangle', 'star', 'circle', 'square', 'cross', 'heart']
custom_shapes_contours = dict()
cam_id = 0 # 0 for default camera
frame_widths = [160,176,320,352,432,544,640,800,960,1184,1280]
custom_shape_sim_threshold = 0.08


# Detects polygon with 3, 4, 5 or many sides in passed contour
def detect_polygon(c):
    shape = None
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)

    if len(approx) == 3:
        return "triangle"
    elif len(approx) == 4:
        return "rectangle"
    elif len(approx) == 5:
        return "pentagon"
    else:
        return "circle"


# Loads binary images of custom shapes from the saved files
# so we can then recognise the patterns in new images coming
# from the camera
def load_custom_shapes():
    for n in custom_shapes_names:
        img = cv2.imread(n + '.png')
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        custom_shapes_contours[n] = contours[0]


# Detects any custom (loaded from files) shapes in passed contour
def detect_custom_shape(c_unknown):
    similarities = dict()
    
    for n, c_shape in custom_shapes_contours.items():
        sim = cv2.matchShapes(c_unknown, c_shape, cv2.CONTOURS_MATCH_I1, 0.0)
        similarities[n] = sim

    sim_values = similarities.values()
    min_sim = min(sim_values)
    if min_sim > custom_shape_sim_threshold:
        return None
    else:
        for n, s in similarities.items():
            if s == min_sim:
                return n


# Returns a camera object with all important parameters set 
# (resolution, FPS, contrast, B&W, etc)
def setup_camera():
    camera = cv2.VideoCapture(cam_id)
        
    if not(camera.isOpened()):
        camera.open()

    # Property codes from here:
    # https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture-set
    # REMEMBER to REMOVE the 'CV_' prefix
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
    camera.set(cv2.CAP_PROP_FPS, 30.0)
    camera.set(cv2.CAP_PROP_CONTRAST, 0.6)
    camera.set(cv2.CAP_PROP_SATURATION, 0.0)
    camera.set(cv2.CAP_PROP_GAIN, 0.0)
    return camera


# Scans custom shapes using the camera and saves them into files. 
# Does not overwrite existing files.
def capture_custom_shapes():
    for n in custom_shapes_names:
        fname = n + '.png'
        if not os.path.isfile(fname): 
            wait_time = 3
            for i in range(wait_time):
                print("Taking a shot of {} in {}...".format(n, wait_time - i))
                sleep(1)

            cam = setup_camera()
            r, img_raw = cam.read()
            cam.release()
            img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
            img = cv2.GaussianBlur(img, (5, 5), 0)
            (thresh, img) = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY_INV)
            
            cv2.imwrite(fname, img)


# Displays simple live stream coming from the camera.
def stream_from_camera(camera):
    while(camera.isOpened()):
        ret, frame = camera.read()
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break    


look_back_window = 3
previously_seen = Queue(maxsize=look_back_window)
while not previously_seen.full():
    previously_seen.put('some strange unidentifiable shape')

def pick_shapes_present_in_stream(custom_shapes):
    if previously_seen.full():
        previously_seen.get()
    
    previously_seen.put(custom_shapes)
    
    previously_seen_list = list(previously_seen.queue)
    shapes_seen_consistently = set()
    for shape in custom_shapes_names:
        seen_consistently = True
        for shapes_set in previously_seen_list:
            if shape not in shapes_set:
                seen_consistently = False
                break
        if seen_consistently:
            shapes_seen_consistently.add(shape)

    return shapes_seen_consistently

def stream_and_detect(camera, displayStream=False):
    

    # Processes the live stream, for every snapshot detecting the shapes.
    while True:        
        # Get fresh image from camera
        r, img_raw = camera.read()
        img_labelled = img_raw

        # Pre-process the image
        img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
        img = cv2.GaussianBlur(img, (5, 5), 0)
        (thresh, img) = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY_INV)
        
        # Find all contours in the image
        img, contours, hierarchy = cv2.findContours(img, 
            cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        polygons = []
        custom_shapes = set()

        # Loop through found contours and try detecting those 
        # that resemble custom shapes or polygons.
        for c in contours:            
            # Detect and remember all detected shapes
            poly_label = detect_polygon(c)
            polygons.append(poly_label)
            custom_shape_label = detect_custom_shape(c)
            if custom_shape_label:
                custom_shapes.add(custom_shape_label)
            
            if displayStream:
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

        if displayStream:
            # Show the captured image with added shape contours 
            # and possibly shape labels as well
            cv2.imshow("Image", img_labelled)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # See in command line what we've found (less resource-intensive 
        # alternative of showing the contours and labels in the original image)
        # print("Polygons: {}".format(polygons))        
        shapes_really_present = pick_shapes_present_in_stream(custom_shapes)
        print("Shapes present: {}".format(shapes_really_present))

        # if cross here check array motor run
        # if 'cross'in shapes_really_present:
        #     ev3.Sound.beep()

        sleep(0.5)


capture_custom_shapes()
load_custom_shapes()
camera = setup_camera()
stream_and_detect(camera, displayStream=True)

camera.release()
cv2.destroyAllWindows()