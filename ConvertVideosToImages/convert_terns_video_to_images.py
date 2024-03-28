import cv2
import os
import shutil
import pytesseract
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date, time
from roboflow import Roboflow
from PIL import Image
from TrackingTerns.iou_boxes_manager import iouBoxesManager
from Utilities.global_utils import GeneralUtils


tour_start_time = time(14, 0, 4)

rf = Roboflow(api_key='CfWQkzWfxMa7Wpcq9WnP')
project = rf.workspace().project("terns-detection")
model = project.version(1).model

# Specify the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust the path according to your installation

def what_is_frame_time(frame):
    # Crop the image using the provided coordinates
    displayed_time = frame[28:55, 1110:1230]

    # Preprocess the image (you can add more steps as needed)
    gray_image = cv2.cvtColor(displayed_time, cv2.COLOR_BGR2GRAY)
    threshold_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Perform OCR using pytesseract
    custom_config = r'--oem 3 --psm 6 outputbase digits'  # Specify OCR engine mode and page segmentation
    text = pytesseract.image_to_string(threshold_image, config=custom_config)

    text = re.sub(r"[^0-9]", "", text) # Keep only numbers in string

    # Check if the extracted text contains at least 6 characters (HH:MM:SS format)
    if len(text) != 6:
        return None
    
    # Extract hours, minutes, and seconds from the recognized text
    hours = int(text[:2])
    minutes = int(text[2:4])
    seconds = int(text[4:6])

    if 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59:
        # Create and return a datetime.time object
        return time(hours, minutes, seconds)
    else:
        return None

def calc_difference(time1, time2):
    # Create datetime objects with a common date (use any date, it won't affect the time difference)
    datetime1 = datetime.combine(datetime.today(), time1)
    datetime2 = datetime.combine(datetime.today(), time2)

    # Calculate the difference between the two time objects
    time_difference = datetime2 - datetime1
    # Return the difference in seconds
    return int(time_difference.total_seconds())

def seconds_to_frames(cap, seconds_number):
  return seconds_number * int(cap.get(cv2.CAP_PROP_FPS))

def display_frame(frame):
    # Display the image using matplotlib
    plt.imshow(frame)
    plt.axis('off')  # Turn off axis labels and ticks
    plt.show()

def frame_changeability(current_frame, previous_frame):
    previous_frame = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
    current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

    flow = cv2.calcOpticalFlowFarneback(previous_frame, current_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
    mean_magnitude = np.mean(magnitude)
    
    return mean_magnitude


def skip_seconds(cap, seconds_number):
  frames_num = seconds_to_frames(cap, seconds_number) # Get frames number in the seconds ammount
  counter = 0
  success = True
  while success and counter < frames_num:
    success,_ = cap.read()
    counter = counter + 1

def skip_till_next_flag(video):
    mean_magnitude_threshold = 3
    previous_frame = None
    is_camera_moving = True
    object_detections_in_frames = []
    while is_camera_moving:
        ret, frame = video.read()         
        predictions = model.predict(frame, confidence=5, overlap=30).json()['predictions']
        current_predictions = [{ 'x': prediction['x'], 'y': prediction['y'], 'width': prediction['width'], 'height': prediction['height']} \
                     for prediction in predictions]

        if len(object_detections_in_frames) < 6:
            object_detections_in_frames.append(current_predictions)
        else:
            iou_boxes_manager = iouBoxesManager()
            print(len(object_detections_in_frames))
            print(len(current_predictions))
            iou = iou_boxes_manager.calc_iou_boxes_seq_vs_boxes_sequences(\
                current_predictions, object_detections_in_frames)
            print(f'Camera moves - {iou}')
            object_detections_in_frames.pop(0)
            object_detections_in_frames.append(current_predictions)
            if iou > 0.04:
                is_camera_moving = False


def skip_into_tour(video):
    is_tour_found = False
    is_skip_done = False
    while not is_tour_found:
        ret, frame = video.read()
        frame_time = what_is_frame_time(frame)
        if frame_time is None:
            continue
        difference_in_sec = calc_difference(frame_time, tour_start_time)

        if not is_skip_done and difference_in_sec > 0:
            print(f'Skipping {difference_in_sec} seconds..')
            skip_seconds(video, difference_in_sec - 1)                
            is_skip_done = True
            continue
        
        if tour_start_time.minute == frame_time.minute and tour_start_time.second == frame_time.second:
            print('Tour part found..')
            is_tour_found = True
        else:
            continue

def calc_frame_diff(old_frame, new_frame):
    # Calculate the absolute difference between frames
    frame_diff = cv2.absdiff(old_frame, new_frame)
    # Convert the difference to grayscale
    gray_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
    # Apply a threshold to the grayscale difference image
    _, threshold_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
    # Count the number of white pixels in the thresholded difference image
    movement_count = cv2.countNonZero(threshold_diff)

    return movement_count    

# This function check if average of any combination of all items exept one item is lower than a threshold
def is_there_low_average(lst, threshold):
    if len(lst) <= 1:
        return False  # Return False if the list has 0 or 1 element
    for i in range(len(lst)):
        combination_sum = sum(lst) - lst[i]
        combination_count = len(lst) - 1
        combination_average = combination_sum / combination_count
        if combination_average < threshold:
            return True

    return False

def extract_frames(video_path, output_path):
    # Extract the base filename from the path
    filename = os.path.basename(video_path)
    # Remove the file extension
    filename_without_extension = os.path.splitext(filename)[0]
    # Open the video file
    video = cv2.VideoCapture(video_path)
    
    fps = video.get(cv2.CAP_PROP_FPS)

    frame_count = 0
    elapsed_time = 0
    flag_number = 1
    seconds_passed_in_flag = 0
    iou_threshold = 0.03
    iou_list = []

    object_detections_in_frames = []

    # Skip to the frame when tour starts
    skip_into_tour(video)

    is_tour_ended = False
    while not is_tour_ended:
        if curr_frame:
            old_frame = curr_frame
        # Read a frame from the video
        ret, curr_frame = video.read()
        if not ret:
            break
        
        if seconds_passed_in_flag > 15:
            predictions = model.predict(curr_frame, confidence=5, overlap=30).json()['predictions']
            current_predictions = [{ 'x': prediction['x'], 'y': prediction['y'], 'width': prediction['width'], 'height': prediction['height']} \
                     for prediction in predictions]

            if len(object_detections_in_frames) < 7:
                object_detections_in_frames.append(current_predictions)
            else:
                iou_boxes_manager = iouBoxesManager()
                iou = iou_boxes_manager.calc_iou_boxes_seq_vs_boxes_sequences(\
                    current_predictions, object_detections_in_frames)
                print(iou)
                if len(iou_list) == 3:
                    iou_threshold = (sum(iou_list)/len(iou_list)) / 3
                    print('iou_threshold:',iou_threshold)
                if len(iou_list) < 4:
                    iou_list.append(iou)
                else:
                    iou_list.pop(0)
                    iou_list.append(iou)

                    if old_frame:
                        diff = calc_frame_diff(old_frame, curr_frame)           
                    else:
                        diff = 0
                        
                    print(diff)

                    if is_there_low_average(iou_list, iou_threshold):
                        # Camera start moving
                        skip_till_next_flag(video)
                        flag_number = flag_number + 1
                        seconds_passed_in_flag = 0                        
                        iou_list = []
                        continue

        # Calculate the current time in seconds
        current_time = frame_count / fps
        
        # Check if one second has passed
        if current_time >= elapsed_time + 1:
            # Generate the output filename
            filename = f"flag{flag_number}_{int(seconds_passed_in_flag)}_{filename_without_extension}.jpg"
            output_filename = output_path + filename
            try:
                # Save the frame as an image
                cv2.imwrite(output_filename, curr_frame)
                print(f'flag #{flag_number}, image #{int(seconds_passed_in_flag)}')
            except Exception as e:
                print(f"Error saving image: {output_filename}")
                print(f"Exception: {e}")
            elapsed_time += 1
            seconds_passed_in_flag += 1
            object_detections_in_frames = []
            
        frame_count += 1

    # Release the video file
    video.release()


# Usage example
video_path = r"C:\\Users\\אייל\\Videos\\test\\atlitcam191.stream_2023_07_21_15_00_00.mkv"
images_output = "./images_output/"

video_name = os.path.splitext(os.path.basename(video_path))[0]
dir_utils = GeneralUtils()
dir_utils.create_directory(images_output + video_name + '/')
extract_frames(video_path, images_output + video_name + '/')