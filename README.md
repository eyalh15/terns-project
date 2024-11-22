# Project Title
Automatic Detecting and counting endangered colonial breeding terns using machine learning methods

## Description
This project leverages Machine Learning methods to automatically detect and count endangered Little Tern and Common Tern species at a breeding site in Israel. Using YOLO V8 for object detection and spatial calibration techniques, we accurately identify individuals and detect breeding terns. The system processes daily camera scans that convers the island area and tracks breeding terns based on consistent location behavior. Our automated approach improves the reliability of population monitoring and enhances conservation efforts.

## How to Run the Project
To run the project, follow these steps to execute each notebook in the correct order.
<!--  -->
### 1. run_video_converter.ipynb Notebook: Video-to-Image Conversion and Position Categorization
This notebook converts video scans captured at the colony into images and detects camera switches to categorize the images by position. It supports a conversion of multiple scans within a video, organizing them into separate directories.

#### Steps
1. Navigate to the ConvertVideoToImage directory.
2. Specify the following settings in the run_video_converter.ini file:
    * **dates**: Dates you want to process.
    * **yolo_path**: Path to Yolo model used for detecting camera movement.
3. Specify the following settings in the tours_details.json file:
    * **videos_dir**: Path to the videos directory.
    * **images_dir**: Path to the output images directory.
4. Open the run_video_converter.ipynb notebook.
5. Run all cells.
<!--  -->
### 2. yolo_runner.ipynb Notebook: YOLO Object Detection on Images
This notebook applies the YOLO V8 object detection model to the categorized images from Notebook 1. The model is trained to detect the terns in each image. The results save for further analysis.

#### Steps
1. Navigate to the YoloDetector directory.
2. Specify the following settings in the yolo_runner.ini file:
    * **dates**: Dates on which you want to detect terns.
    * **images_dir**: Path to the input image directory.
    * **result_dir**: Path to the output YOLO detection results directory.
    * **images_chunk_size**: Number of images to process at one time in YOLO.
4. Open the yolo_runner.ipynb notebook.
5. Run all cells.

<!--  -->
### 3. track_scan_runner.ipynb Notebook: Tracking Terns in a Single Scan
This notebook processes a one scan output from YOLO Object Detection to track individual terns across multiple images, creating a sequence of detections for each bird.

#### Steps
1. Navigate to the TrackingTerns directory.
2. Specify the following settings in the track_scan_runner.ini file:
    * **dates**: Dates on which you want to track terns.
    * **yolo_result_dir**: Path to the input YOLO results directory.
    * **tracker_result_dir**: Path to the output tracking results directory.
3. Open the track_scan_runner.ipynb notebook.
4. Run all cells.


### 4. daily_count_terns.ipynb Notebook: Daily Counting and Classifying of Terns
This notebook classify and counts terns on colony on multiple one-scan outputs from one day. It makes aggregation of the results across different scans.

1. Navigate to the ClassifyingTerns directory.
2. Specify the following settings in the daily_count_terns.ini file:
    * **date**: Date for which you want to classify and count terns.
    * **classifier_model**: Path to the trained classifier model.
    * **tracker_result_dir**: Path to the tracking results directory.
    * **labels_distribution**: Path to the label distributions statistics file.
3. Open the daily_count_terns.ipynb notebook.
4. Run all cells.



## Detecting breeding terns
<!--  -->
### 5. track_breeding_terns_runner.ipynb Notebook: Tracking Breeding Terns
This notebook processes multiple one-scan outputs from part 3 to track terns across multiple scans. The tracks help identify breeding terns, which tend to remain in the same location over time.

1. Navigate to the TrackingTerns directory.
2. Specify the following settings in the track_breeding_terns.ini file:
    * **date**: A date for which you want to track breeding terns.
    * **one_scan_result_dir**: Path to the input single-scan tracking results directory.
    * **mult_scans_result_dir**: Path to the output directory for multi-scan tracking results.
    * **images_dir**: Path to the images directory.
3. Open the track_breeding_terns_runner.ipynb notebook.
4. Run all cells.

<!--  -->
### 6: count_breeding_terns.ipynb Notebook: Classifying and counting breeding terns
This notebook classifies and counts breeding terns within the colony, using tracking data from Part 5 as input.

1. Navigate to the ClassifyingTerns directory.
2. Specify the following settings in the count_breeding_terns.ini file:
    * **date**: Date for which you want to classify and count breeding terns.
    * **classifier_model**: Path to trained classifier model.
    * **overlap_areas**: Path to the overlap areas file.
    * **breeding_tracks_dir**: Path to the breeding terns tracking results directory.
    * **labels_distribution**: Path to the label distributions statistics file.
4. Open the count_breeding_terns.ipynb notebook.
5. Run all cells.