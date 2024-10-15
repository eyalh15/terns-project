# Project Title
Automatic Detecting and counting endangered colonial breeding birds using machine learning methods

## Description
This project leverages Machine Learning methods to automatically detect and count endangered Little Tern and Common Tern species at a breeding site in Israel. Using YOLO V8 for object detection and spatial calibration techniques, we accurately identify individuals and detect breeding birds. The system processes daily camera scans that convers the island area and tracks breeding birds based on consistent location behavior. Our automated approach improves the reliability of population monitoring and enhances conservation efforts.

## How to Run the Project
To run the project, follow these steps to execute each notebook in the correct order. Ensure that your environment is configured properly before running the notebooks.

### Prerequest
Install the required dependencies by running `pip install -r requirements.txt`.

### Notebook 1: Video to Image Conversion and Position Categorization
This notebook convert a scans videos captured at the colony into images and also detects camera switches to categorize the images by position. The notebook can handle conversion of a video containing multiple scans and recognize and seperate them into different dirs.  
The notebook read the video 
#### Steps

1. Navigate to the ConvertVideoToImages directory.
2. Specify the paths for the videos directory(videos_dir) and the output image directory(images_dir) in the tours_details.json file.
3. Specify the dates you want to process in the run_video_converter.ini file.
4. Open the run_video_converter.ipynb notebook.
5. Run all cells.

### Notebook 2: Run Yolo Object Detector on Images
This notebook applies the YOLO V8 object detection model to the categorized images from Notebook 1. The model is trained to detect Little Tern and Common Tern species in each image. After detection, it produces bounding boxes around the birds and saves the results for further analysis.
#### Steps

1. Navigate to the YoloDetector directory.
2. Specify the paths for the input image directory (images_dirs) and the output results directory(result_dir) in the yolo_runner.ini file.
3. Specify the dates you want to detect terns on in the yolo_runner.ini file.
4. Open the yolo_runner.ipynb notebook.
5. Run all cells.


### Notebook 3: Tracking Birds in one Scan
This notebook processes a one scan output from YOLO Object Detection to track individual birds across multiple images, creating a sequence of detected boxes for each bird.

1. Navigate to the TrackingTerns directory.
2. Specify both paths for input YOLO results (yolo_result_dir) and output results directory (tracker_result_dir) in the track_movie_runner.ini file.
3. Specify the dates on which you want to track terns in the track_movie_runner.ini file.
4. Open the track_movie_runner.ipynb notebook.
5. Run all cells.


### Notebook 4: Daily Count breeding birds
This notebook processes multiple one-scan outputs to to track individual birds across different times and locations. Identifying birds that appear in the same location across different scans to detect breeding birds. It creates a sequence of bounding boxes across multiple scans for each bird.

1. Navigate to the DecisionTreeClassifier directory.
2. Specify paths for the input YOLO results (yolo_result_dir) and the output results directory (tracker_result_dir) in the track_movie_runner.ini file
3. Specify the dates on which you want to track terns in the track_movie_runner.ini file.
4. Open the daily_count_brooders.ipynb notebook.
5. Run all cells.


### Notebook 4: Tracking Individual Breeding Birds Across Multiple Scans
This notebook processes multiple one-scan outputs to to track individual birds across different times and locations. Identifying birds that appear in the same location across different scans to detect breeding birds. It creates a sequence of bounding boxes across multiple scans for each bird.

1. Navigate to the TrackingTerns directory.
2. Specify paths for the input YOLO results (yolo_result_dir) and the output results directory (tracker_result_dir) in the track_movie_runner.ini file
3. Specify the dates on which you want to track terns in the track_movie_runner.ini file.
4. Open the yolo_runner.ipynb notebook, where you'll likely process the images for bird detection using YOLO.
5. Run all cells.

### Notebook 5: Aggregate multiple scans results and display terns count in one day
<!-- This notebook processes multiple one-scan outputs to to track individual birds across different times and locations. Identifying birds that appear in the same location across different scans to detect breeding birds. It creates a sequence of bounding boxes across multiple scans for each bird.

1. Navigate to the TrackingTerns directory.
2. Specify paths for the input YOLO results (yolo_result_dir) and the output results directory (tracker_result_dir) in the track_movie_runner.ini file
3. Specify the dates on which you want to track terns in the track_movie_runner.ini file.
4. Open the yolo_runner.ipynb notebook, where you'll likely process the images for bird detection using YOLO.
5. Run all cells. -->

### Notebook 5: Count breeding birds
<!-- This notebook processes multiple one-scan outputs to to track individual birds across different times and locations. Identifying birds that appear in the same location across different scans to detect breeding birds. It creates a sequence of bounding boxes across multiple scans for each bird.

1. Navigate to the TrackingTerns directory.
2. Specify paths for the input YOLO results (yolo_result_dir) and the output results directory (tracker_result_dir) in the track_movie_runner.ini file
3. Specify the dates on which you want to track terns in the track_movie_runner.ini file.
4. Open the yolo_runner.ipynb notebook, where you'll likely process the images for bird detection using YOLO.
5. Run all cells. -->