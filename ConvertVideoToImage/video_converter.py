import os
import sys
import cv2
import json
import configparser
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO


script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
# Add the project root to the Python path
sys.path.append(project_root)
from Utilities.global_utils import GeneralUtils
from TrackingTerns.iou_boxes_manager import iouBoxesManager

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
        
        # Loading the pretrained model
        try:
            self._model = YOLO(yolo_path)
            print(f"Model loaded successfully from {yolo_path}")
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


    def _display_frame(self, frame):
        # Display the image using matplotlib
        plt.imshow(frame)
        plt.axis('off')  # Turn off axis labels and ticks
        plt.show()
        

    def frame_changeability(self, current_frame, previous_frame):
        previous_frame = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(previous_frame, current_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mean_magnitude = np.mean(magnitude)
        
        return mean_magnitude

    def _calc_difference_between_frames(self, frame1, frame2):
        # Calculate the absolute difference between frames
        frame_diff = cv2.absdiff(frame1, frame2)

        # Convert the difference to grayscale
        gray_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)

        # Apply a threshold to the grayscale difference image
        _, threshold_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

        # Count the number of white pixels in the thresholded difference image
        return cv2.countNonZero(threshold_diff)


    def _skip_seconds(self, video, seconds_number):
        print(f'Skipping {seconds_number} seconds..')
        frames_num = self._seconds_to_frames(seconds_number) # Get frames number in the seconds ammount
        success = True
        counter = 0
        print(seconds_number, frames_num)
        while success and counter < frames_num:
            success,_ = video.read()
            counter = counter + 1


    def _skip_till_next_flag(self, video):
        is_camera_moving = True
        object_detections_in_frames = []

        while is_camera_moving:
            ret, frame = video.read()         

            try:
                # predict image labels by YOLO model
                result = self._model(frame, show_conf=False, line_width=2, show_labels=True, verbose=False)[0]
            except Exception as e:
                print(f"Error during model inference: {str(e)}")            

            current_predictions = json.loads(result.to_json())

            if len(object_detections_in_frames) < 8:
                object_detections_in_frames.append(current_predictions)
            else:
                iou_boxes_manager = iouBoxesManager()
                # print(len(current_predictions))
                iou = iou_boxes_manager.calc_iou_boxes_seq_vs_boxes_sequences(\
                    current_predictions, object_detections_in_frames)
                # print(f'IOU value - {iou}')
                object_detections_in_frames.pop(0)
                object_detections_in_frames.append(current_predictions)
                if iou > 0.025:
                    is_camera_moving = False


    def _average_box_squares(self, box_list):
        total_area = 0

        for box in box_list:
            x1 = box['box']['x1']
            y1 = box['box']['y1']
            x2 = box['box']['x2']
            y2 = box['box']['y2']

            # Calculate the area of the box
            area = (x2 - x1) * (y2 - y1)

            # Add the square of the area to the total
            total_area += area ** 2

        # Calculate the average of the squares
        average = total_area / len(box_list)

        return average


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
        
        self._skip_seconds(video, 2)


    # This function check how much tours the video length can fit
    def _get_tours_number_in_video(self, video_path, tour_length):
        # Open the video file
        cap = cv2.VideoCapture(video_path)

        # Check if the video file was opened successfully
        if not cap.isOpened():
            raise Exception("Error: Could not open video file")

        # Get the frame rate of the video
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        # fps = 25
        # Get the total number of frames in the video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Close the video file
        cap.release()
        # Calculate the video duration in seconds
        video_duration = total_frames / fps
        # Calculate the number of tours based on the tour length
        num_tours = int(video_duration // tour_length)
        return 2

    def convert_video(self, video_path, video_scan_times, flags_ids, tour_length, magin_between_tours, \
                      margin_till_1st_tour, output_dir):
        # Open video file
        video = cv2.VideoCapture(video_path)

        flags_number = len(flags_ids)
        # Get the frame rate of the video
        fps = int(video.get(cv2.CAP_PROP_FPS))
        fps = 25 if fps == 1000 else fps
        # Extract video name from path
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        # Calculate tours number in video according to video length
        tours_number = self._get_tours_number_in_video(video_path, tour_length)

        self._skip_seconds(video, margin_till_1st_tour - 4) 
        _, curr_frame = video.read()
        cv2.imwrite('after_skip_dead_time.png', curr_frame)

        for tour_num in range(tours_number):
            # Skip tour if it already exist
            if os.path.exists(f'{output_dir}/{video_name}/tour{tour_num}'):
                self._skip_seconds(video, 82 + tour_length)
                continue
            
            # Create dir for tour images
            utils_lib = GeneralUtils()
            utils_lib.create_directory(f'{output_dir}/{video_name}/tour{tour_num}')

            frame_count = 0
            flag_index = 0
            moves_detect_iterate_cnt = 0
            seconds_passed_in_flag = 0
            min_frames_in_flag = 12
            iou_threshold = 0.03
            iou_list = []
            object_detections_in_frames = []


            if tour_num > 0:
                self._skip_seconds(video, magin_between_tours - 5)

            # Skip to the frame when tour starts
            self._skip_into_tour(video)
            _, curr_frame = video.read()
            # cv2.imwrite('tour_will_start.png', curr_frame)            

            is_tour_ended = False
            while not is_tour_ended:
                # Read a frame from the video
                _, curr_frame = video.read()
                
                if seconds_passed_in_flag > min_frames_in_flag:

                    moves_detect_iterate_cnt += 1
                    if moves_detect_iterate_cnt % 22 == 0:
                        object_detections_in_frames = []
                    try:
                        # predict image labels by YOLO model
                        result = self._model(curr_frame, show_conf=False, line_width=2, show_labels=True, verbose=False)[0]
                    except Exception as e:
                        print(f"Error during model inference: {str(e)}")            

                    current_predictions = json.loads(result.to_json())
                    if len(object_detections_in_frames) < 4:
                        object_detections_in_frames.append(current_predictions)
                        moves_detect_iterate_cnt = 0
                    else:
                        iou_boxes_manager = iouBoxesManager()
                        # Calculate IOU between current image detections and previous detections
                        iou = iou_boxes_manager.calc_iou_boxes_seq_vs_boxes_sequences(\
                            current_predictions, object_detections_in_frames)
                        
                        if len(iou_list) < 4:
                            iou_list.append(iou)
                            if len(iou_list) == 4:
                                iou_threshold = (sum(iou_list)/len(iou_list)) / 3
                        else:
                            iou_list.pop(0)
                            iou_list.append(iou)                    

                            all_zero_ious = not np.any(iou_list)

                            if (not all_zero_ious and self._is_iou_under_threshold(iou_list, iou_threshold)) \
                                or seconds_passed_in_flag > 17:

                                if flag_index >= flags_number - 1:
                                    is_tour_ended = True          
                                else:
                                    if flags_ids[flag_index] == 137:
                                        min_frames_in_flag = 5
                                    else:
                                        min_frames_in_flag = 12

                                    if flags_ids[flag_index] == 123:
                                        camera_move_time = 7
                                    elif flags_ids[flag_index] == 49:
                                        camera_move_time = 4
                                    elif flags_ids[flag_index] == 52:
                                        camera_move_time = 4
                                    elif flags_ids[flag_index] == 83:
                                        camera_move_time = 5                                            
                                    else:
                                        camera_move_time = 2
                                    
                                    
                                    self._skip_seconds(video, camera_move_time)
                                    seconds_passed_in_flag = 0                        
                                    iou_list = []

                                flag_index = flag_index + 1                                    
                                continue
                
                # Check if one second has passed
                if frame_count >= fps:
                    # Generate the output filename
                    filename = f"flag{flags_ids[flag_index]}_{int(seconds_passed_in_flag)}_{video_name}.jpg"
                    output_filename = f'{output_dir}/{video_name}/tour{tour_num}/{filename}'
                    try:
                        # Save the frame as an image
                        cv2.imwrite(output_filename, curr_frame)
                        print(f'flag #{flags_ids[flag_index]}, image #{int(seconds_passed_in_flag)}')
                    except Exception as e:
                        print(f"Error saving image: {output_filename}")
                        print(f"Exception: {e}")
                        
                    seconds_passed_in_flag += 1
                    object_detections_in_frames = []
                    frame_count = 0
                    
                frame_count += 1
            
        # Release the video file
        video.release()