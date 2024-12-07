import os
import sys
import cv2
import json
import configparser

from ultralytics import YOLO
from collections import defaultdict

from tour_extraction_validator import TourExtractionValidator



script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
# Add the project root to the Python path
sys.path.append(project_root)
from Utilities.global_utils import GeneralUtils
from TrackingTerns.iou_boxes_manager import iouBoxesManager


camera_move_time = defaultdict(lambda: 2, {
    40: 4, 45: 4, 49: 6, 52: 6, 57: 4, 59: 4, 68: 5, 71: 4, 4: 5, 79: 4, 82: 5, 84: 5,
    111: 6, 117: 7, 119: 7, 123: 9, 127: 5, 136: 4
})

max_displayed_frames = defaultdict(lambda: 11, {
    138: 9
})

class VideoConverter:
    def __init__(self):
        config = configparser.ConfigParser()
        # Read the config file
        config.read('run_video_converter.ini', encoding="utf8")
        # Load a model
        yolo_path = config.get('General', 'yolo_path').replace('\\', '/')
        # Check if model file exists
        if not os.path.exists(yolo_path):
            print(f"Model path does not exist: {yolo_path}")
            exit()
        
        self._tour_extract_validator = TourExtractionValidator()
        
        # Loading the pretrained model
        try:
            self._model = YOLO(yolo_path)
        except Exception as e:
            print(f"Error loading model from {yolo_path}: {str(e)}")


    # This function check if average of any combination of all items exept one item is lower than a threshold
    def _is_iou_under_threshold(self, lst, threshold):
        if len(lst) <= 1:
            return False  # Return False if the list has 0 or 1 element
        for i in range(len(lst)):
            combination_sum = sum(lst) - lst[i]
            combination_count = len(lst) - 1
            combination_average = combination_sum / combination_count
            if combination_average < threshold:
                return True

        return False

        
    def _seconds_to_frames(self, seconds_number):
        return seconds_number * 25


    def _skip_seconds(self, video, seconds_number):
        frames_num = self._seconds_to_frames(seconds_number) # Get frames number in the seconds ammount
        success = True
        counter = 0
        while success and counter < frames_num:
            success,_ = video.read()
            counter = counter + 1


    def _skip_into_tour(self, video):     
        object_detections_in_frames = []
        iou_list = []
        is_tour_found = False
        count_frames = 0
        ret = None
        while not is_tour_found:
            ret, curr_frame = video.read()
            if not ret:
                print("Error: Failed to capture frame from video.")
                exit()

            count_frames += 1

            if count_frames % 100 == 0:
                object_detections_in_frames = []
                iou_list = []

            try:
                # predict image labels by YOLO model
                result = self._model(curr_frame, show_conf=False, line_width=2, show_labels=True, verbose=False)[0]
            except Exception as e:
                print(f"Error during model inference: {str(e)}")            
                            
            current_predictions = json.loads(result.to_json())

            if len(current_predictions) == 0:
                continue

            if len(object_detections_in_frames) < 7:
                object_detections_in_frames.append(current_predictions)
            else:
                iou_boxes_manager = iouBoxesManager()
                iou = iou_boxes_manager.calc_iou_boxes_seq_vs_boxes_sequences(\
                    current_predictions, object_detections_in_frames)
                if len(iou_list) == 3:
                    iou_threshold = (sum(iou_list)/len(iou_list)) / 8
                if len(iou_list) < 4:
                    iou_list.append(iou)
                else:
                    iou_list.pop(0)
                    iou_list.append(iou)

                    if self._is_iou_under_threshold(iou_list, iou_threshold):
                        # Camera start moving
                        is_tour_found = True
                        continue
        
        self._skip_seconds(video, 6)


    # This function check how much tours the video length can fit
    def _calc_tours_number(self, video_path, tour_length, fps):
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        # Check if the video file was opened successfully
        if not cap.isOpened():
            raise Exception("Error: Could not open video file")
        # Get the total number of frames in the video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Close the video file
        cap.release()
        # Calculate the video duration in seconds
        video_duration = total_frames / fps
        # Calculate the number of tours based on the tour length
        return int(video_duration // tour_length)


    def convert_video(self, video_path, flags_ids, tour_length, magin_between_tours, \
                      margin_till_1st_tour, output_dir):
        # Open video file
        video = cv2.VideoCapture(video_path)

        flags_number = len(flags_ids)
        # Get the frame rate of the video
        fps = int(video.get(cv2.CAP_PROP_FPS))
        fps = 25 if fps == 1000 else fps
        tours_number = 2

        # Skip margin time before first tour start
        self._skip_seconds(video, margin_till_1st_tour - 4) 
        _, curr_frame = video.read()
        # Extract video name from path
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        utils_lib = GeneralUtils()
        for tour_num in range(tours_number):
            tour_dir = f'{output_dir}/{video_name}/tour{tour_num}/'
            # Skip tour if it already exist
            if os.path.exists(tour_dir):
                self._skip_seconds(video, 82 + tour_length)
                continue
            
            # Create dir for tour images
            utils_lib.create_directory(tour_dir)

            frame_num = 0
            # Skip to the frame when tour starts
            self._skip_into_tour(video)
            _, curr_frame = video.read()
            cv2.imwrite('tour_will_start.png', curr_frame)            

            frames_counter = 0
            flag_num = 0
            while flag_num < flags_number:
                # Read a frame from the video
                _, curr_frame = video.read()
                # Check if one second has passed
                if frames_counter % fps == 0:
                    # Generate the output filename
                    filename = f"flag{flags_ids[flag_num]}_{int(frame_num)}_{video_name}.jpg"
                    output_filename = f'{output_dir}/{video_name}/tour{tour_num}/{filename}'
                    try:
                        # Save the frame as an image
                        cv2.imwrite(output_filename, curr_frame)
                    except Exception as e:
                        print(f"Exception: {e}")

                    frame_num += 1

                # If the frame is the last
                if frame_num > max_displayed_frames[flags_ids[flag_num]]:
                    # Skip to next frame (2 seconds is the default move time)
                    self._skip_seconds(video, camera_move_time[flags_ids[flag_num]] + 3.34 - 0.461)
                    flag_num += 1
                    frame_num = 0
                
                frames_counter += 1

            try:
                if not self._tour_extract_validator.is_valid_tour(tour_dir):
                    print('deleting...', tour_dir)
                    # utils_lib.delete_directory(tour_dir)
            except Exception as e:
                print(f"Error: {e}")
        
        # Delete video tours dir if all tours are invalid
        try:
            tours_dir = f'{output_dir}/{video_name}'
            if(os.path.is_dir(tours_dir) and len(os.listdir(tours_dir)) == 0):
                utils_lib.delete_directory(tour_dir)
        except Exception as e:
            print(f"Error: {e}")
        



            
        # Release the video file
        video.release()