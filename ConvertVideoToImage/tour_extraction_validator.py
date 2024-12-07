import os
import cv2
import json
import numpy as np

from PIL import Image


# Directory containing the final flag images and key areas coordinates JSON
FINAL_FLAG_IMAGES_DIR = '/content/drive/MyDrive/tern_project/Eyal/ConvertVideoToImage/FinalFlagSamples/'

# The TourExtractionValidator class validates the extraction process of camera tours,
# checking if the camera positions match the expected final flag positions.
class TourExtractionValidator:
    def __init__(self, threshold=0.85):
        self._threshold = threshold

        # Load the key areas configuration from JSON
        with open(FINAL_FLAG_IMAGES_DIR + 'key_areas.json', 'r') as file:
            key_areas_data = json.load(file)
        
        self._key_areas = self._read_key_areas(key_areas_data)
    
    
    # Reads and processes the key areas from the key_areas_data JSON
    def _read_key_areas(self, key_areas_data):
        # Load grayscale final images for each camera
        final_images = {
            cam_id: cv2.imread(FINAL_FLAG_IMAGES_DIR + cam_id + '.jpg', cv2.IMREAD_GRAYSCALE)
            for cam_id in key_areas_data.keys()
        }
        # Map coordinates to cropped areas from final images
        return {
            cam_id: {
                'final_flag': flag_details['flag_id'],
                'areas_coords': {
                    tuple(coordinates): self._cropImage(final_images[cam_id], *coordinates)
                    for coordinates in flag_details['coords']
                }
            }
            for cam_id, flag_details in key_areas_data.items()
        }


    # Crops a specific region from an image based on coordinates
    def _cropImage(self, img, x, y, w, h):
        return img[y:y + h, x:x + w]


    # Checks if the given image corresponds to the final flag for the specified camera
    def _is_final_flag(self, images_paths, cam_id):
        for image_path in images_paths:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Image not found: {image_path}")

            # Get key areas for the camera
            key_areas = self._key_areas[cam_id]['areas_coords']
            
            overall_diff = 0
            # Calculate the overall difference between key areas and the image
            for coords in key_areas:
                cropped1 = self._cropImage(image, *coords)
                cropped2 = key_areas[coords]
                # Calucalte distancce between cropped images
                diff_mat = np.maximum(cropped1, cropped2) - np.minimum(cropped1, cropped2)
                overall_diff += (np.mean(diff_mat) / 255) # 255 is the maximum value

        similarity = (1 - (overall_diff / (len(key_areas) * len(images_paths))))

        return similarity > self._threshold

    # Validates if the tour in the specified directory ends at the final flag
    def is_valid_tour(self, tour_dir):
        cam_id = None
        # Determine the camera ID from the directory name
        for flag in self._key_areas.keys():
            if flag in tour_dir:
                cam_id = flag

        if not cam_id:
            raise ValueError("tour_dir path is invalid.")

        if not os.path.exists(tour_dir):
            raise FileNotFoundError(f"Directory does not exist: {tour_dir}")

        # Get images related to the final flag from the tour directory
        last_flag_images = [tour_dir + image_name for image_name in os.listdir(tour_dir)  \
                 if str(self._key_areas[cam_id]['final_flag']) in image_name]
        
        # Return False if no images from the final flag are found
        if len(last_flag_images) == 0:
            return False

        # Validate the first and last images of the final flag
        images_edges = [last_flag_images[0], last_flag_images[-1]]

        return self._is_final_flag(images_edges, cam_id)