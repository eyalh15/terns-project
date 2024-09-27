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
3. Specify the paths for the videos directory(videos_dir) and the output image directory(images_dir) in the tours_details.json file.
3. Specify the dates you want to process in the convert_terns_video_to_images.ini file.
4. Open the run_video_converter.ipynb notebook.
5. Run all cells to convert the videos into categorized images based on camera positions.

### Notebook 2: Run Yolo Object Detector on Images
This notebook run 
#### Steps

1. Navigate to the ConvertVideoToImages directory.
3. Specify the paths for the videos directory(videos_dir) and the output image directory(images_dir) in the tours_details.json file.
3. Specify the dates you want to process in the convert_terns_video_to_images.ini file.
4. Open the run_video_converter.ipynb notebook.
5. Run all cells to convert the videos into categorized images based on camera positions.