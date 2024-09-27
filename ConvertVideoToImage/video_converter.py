import os
import sys
import cv2
import json
import configparser
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
from scipy.ndimage import measurements


from PIL import Image
from datetime import datetime, date, time


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
        config.read('video_converter.ini', encoding="utf8")
        # Load a model
        model_path = config.get('Yolo', 'model_path').replace('\\', '/')
        self._model = YOLO(model_path) # pretrained YOLOv8n model


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


    def _seconds_to_frames(self, cap, seconds_number):
        return seconds_number * int(cap.get(cv2.CAP_PROP_FPS))


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
        frames_num = self._seconds_to_frames(video, seconds_number) # Get frames number in the seconds ammount
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

            # predict image labels by YOLO model
            result = self._model(frame, show_conf=False, line_width=2, show_labels=True, verbose=False)[0]

            current_predictions = json.loads(result.tojson())

            if len(object_detections_in_frames) < 8:
                object_detections_in_frames.append(current_predictions)
            else:
                iou_boxes_manager = iouBoxesManager()
                print(len(current_predictions))
                iou = iou_boxes_manager.calc_iou_boxes_seq_vs_boxes_sequences(\
                    current_predictions, object_detections_in_frames)
                print(f'IOU value - {iou}')
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
            count_frames += 1
            if count_frames % 100 == 0:
                object_detections_in_frames = []
                iou_list = []
            if count_frames % 1000 == 0:
                self._display_frame(curr_frame)
            # predict image labels by YOLO model
            result = self._model(curr_frame, show_conf=False, line_width=2, show_labels=True, verbose=False)[0]
            
            current_predictions = json.loads(result.tojson())

            # box_square_average = self._average_box_squares(current_predictions)
            # print(box_square_average)

            if len(current_predictions) == 0:
                continue

            if len(object_detections_in_frames) < 7:
                object_detections_in_frames.append(current_predictions)
            else:
                iou_boxes_manager = iouBoxesManager()
                iou = iou_boxes_manager.calc_iou_boxes_seq_vs_boxes_sequences(\
                    current_predictions, object_detections_in_frames)
                print(iou)
                if len(iou_list) == 3:
                    iou_threshold = (sum(iou_list)/len(iou_list)) / 8
                    print(f'iou_threshold:',iou_threshold)
                if len(iou_list) < 4:
                    iou_list.append(iou)
                else:
                    iou_list.pop(0)
                    iou_list.append(iou)

                    if self._is_iou_under_threshold(iou_list, iou_threshold):
                        print('first flag found!!!')
                        # Camera start moving
                        is_tour_found = True
                        continue
        
        ret, curr_frame = video.read()
        cv2.imwrite('before_skip1.png', curr_frame)
        self._skip_seconds(video, 3)
        ret, curr_frame = video.read()
        cv2.imwrite('after_skip1.png', curr_frame)
        

    def _extract_frames(self, video_path, video_scan_times, tour_length, flag_length, output_path):
        print(video_scan_times)
        return

    # This function check how much tours the video length can fit
    def _get_tours_number_in_video(self, video_path, tour_length):
        # Open the video file
        cap = cv2.VideoCapture(video_path)

        # Check if the video file was opened successfully
        if not cap.isOpened():
            raise Exception("Error: Could not open video file")

        # Get the frame rate of the video
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        # Get the total number of frames in the video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Close the video file
        cap.release()
        # Calculate the video duration in seconds
        video_duration = total_frames / fps
        # Calculate the number of tours based on the tour length
        num_tours = int(video_duration // tour_length)
        return num_tours

    def convert_video(self, video_path, video_scan_times, flags_ids, tour_length, magin_between_tours, \
                      margin_till_1st_tour, output_dir):

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        # The directory exist means the video already converted
        print(f'-__-{output_dir}/{video_name}-__-')

        flags_number = len(flags_ids)
        # Recognzie how much tours the video have
        tours_number = self._get_tours_number_in_video(video_path, tour_length)
        
        print(video_name)
        print(tours_number)
        # Open the video file
        video = cv2.VideoCapture(video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        utils_lib = GeneralUtils()
        
        
        self._skip_seconds(video, margin_till_1st_tour - 4) 

        for tour_num in range(tours_number):
            # If tour exist then skip time and continue to next tour
            if os.path.exists(f'{output_dir}/{video_name}/tour{tour_num}'):
                print(f'The tour #{tour_num} exist')
                print('skipping tour..')
                ret, curr_frame = video.read()
                cv2.imwrite('old1.png', curr_frame)
                self._skip_seconds(video, 82 + tour_length)
                ret, curr_frame = video.read()
                cv2.imwrite('new1.png', curr_frame)
                continue
                
            # Create dir for tour images
            utils_lib.create_directory(f'{output_dir}/{video_name}/tour{tour_num}')

            frame_count = 0
            elapsed_time = 0
            flag_index = 0
            moves_detect_iterate_cnt = 0
            seconds_passed_in_flag = 0
            frames_without_cam_move = 12
            iou_threshold = 0.03
            iou_list = []

            object_detections_in_frames = []

            if tour_num > 0:
                self._skip_seconds(video, magin_between_tours - 5)

            # Skip to the frame when tour starts
            self._skip_into_tour(video)

            is_tour_ended = False
            ret = None
            while not is_tour_ended:
                if ret:
                    prev_frame = curr_frame
                # Read a frame from the video
                ret, curr_frame = video.read()
                if not ret:
                    break
                
                if seconds_passed_in_flag > frames_without_cam_move:
                    moves_detect_iterate_cnt += 1
                    if moves_detect_iterate_cnt % 22 == 0:
                        object_detections_in_frames = []
                    # predict image labels by YOLO model
                    result = self._model(curr_frame, show_conf=False, line_width=2, show_labels=True, verbose=False)[0]

                    current_predictions = json.loads(result.tojson())

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
                            print(iou_list, iou_threshold)

                            all_zero_ious = not np.any(iou_list)
                            print(seconds_passed_in_flag)
                            if (not all_zero_ious and self._is_iou_under_threshold(iou_list, iou_threshold)) \
                                or seconds_passed_in_flag > 17:
                                print('Camera start moving..')
                                flag_index = flag_index + 1

                                if flag_index > flags_number - 1:
                                    is_tour_ended = True          
                                else:
                                    print(f'flag id: {flags_ids[flag_index]}')

                                    # frames_without_cam_move = 12 
                                    if flags_ids[flag_index] == 138:
                                        frames_without_cam_move = 5                                                                           
                                    else:
                                        frames_without_cam_move = 12

                                    if flags_ids[flag_index - 1] == 123:
                                        camera_move_time = 7
                                    elif flags_ids[flag_index - 1] == 49:
                                        camera_move_time = 4
                                    elif flags_ids[flag_index - 1] == 52:
                                        camera_move_time = 4
                                    elif flags_ids[flag_index - 1] == 83:
                                        camera_move_time = 5                                            
                                    else:
                                        camera_move_time = 2
                                    
                                    self._skip_seconds(video, camera_move_time)
                                    seconds_passed_in_flag = 0                        
                                    iou_list = []
                                    
                                continue

                # Calculate the current time in seconds
                current_time = frame_count / fps
                
                # Check if one second has passed
                if current_time >= elapsed_time + 1:
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
                    elapsed_time += 1
                    seconds_passed_in_flag += 1
                    object_detections_in_frames = []
                    
                frame_count += 1
            
        # Release the video file
        video.release()