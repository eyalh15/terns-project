import os
import re
import json
import glob
import argparse

from pathlib import Path
from datetime import datetime

from video_converter import VideoConverter

def get_tour_details(video_path, tours_details):
    # Define a regular expression pattern to match the camera ID
    pattern = r'atlit(?:cam)?(\d+)\.stream'
    # Search for the pattern in the file path
    match = re.search(pattern, video_path)
    
    if match:
        camera_id = match.group(1)
        specific_cam_details = None
        camera_name = ''
        for cam_name, cam_detials in tours_details.items():
            if cam_detials["camera_id"] == int(camera_id):
                specific_cam_details = cam_detials
                camera_name = cam_name
                break
        if specific_cam_details is None:
            raise ValueError("The file name does not have camera name as expected: {'191' or '181}")
    else:
        raise ValueError("The file name is not in the format to have the camera name as expected")

    flags_ids = specific_cam_details['flags_ids']
    tour_length = specific_cam_details['tour_length']
    magin_between_tours = specific_cam_details['magin_between_tours']
    margin_till_1st_tour = specific_cam_details['margin_till_1st_tour']
    
    # get the video time from the file name
    video_path_without_extension = os.path.splitext(video_path)[0]
    video_time = video_path_without_extension.split("_")[-3:]
    video_time = "-".join(video_time)
    
    time_format = "%H-%M-%S"
    try:
        video_time = datetime.strptime(video_time, time_format)
    except:
        return (None, None, None, None, None)

    # Recognize what tour session the video have
    sessions_scan_times = specific_cam_details['scan_time']

    min_time_difference = None
    for scan_times in sessions_scan_times.values():
        # start_times[0] have the start time of the first scan in the session
        # Parse time strings into datetime objects
        session_time = datetime.strptime(scan_times[0], time_format)
        
        time_difference = abs((session_time - video_time).total_seconds())
        if min_time_difference is None or min_time_difference > time_difference:
            min_time_difference = time_difference
            video_scan_times = scan_times

    return (video_scan_times, flags_ids, tour_length, margin_till_1st_tour, magin_between_tours)


if __name__=='__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--video_name', help='The name of a video')
    # Read the directory path where videos located
    video_name = parser.parse_args().video_name

    # Read the JSON configuration file
    with open('tours_details.json', 'r', encoding='utf-8') as config_file:
        tour_configuration = json.load(config_file)
    
    videos_dir = Path(tour_configuration["videos_dir"])

    if not videos_dir.exists() or not videos_dir.is_dir():
        print(f'{videos_dir} - Movies directory path does not exist.')
        exit()
    
    video_path = str(videos_dir / video_name)
    print(type(video_path))
    print(video_path)
    
    video_converter = VideoConverter()
    (video_scan_times, flags_ids, tour_length, margin_till_1st_tour, magin_between_tours) = get_tour_details(\
        video_path, tour_configuration['tours_details'])
    if video_scan_times == None or flags_ids == None or tour_length == None:
        exit()
        
    video_converter.convert_video(video_path, video_scan_times, flags_ids, tour_length, magin_between_tours, \
                                    margin_till_1st_tour, tour_configuration['images_dir'])
            