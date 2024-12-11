import os
import re
import cv2
import json
import shutil
import numpy as np

class GeneralUtils:
    @staticmethod
    def _load_json(file_path):
        """
        Helper function to load JSON content from a file.
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON in file: {file_path}")
            return None


    @staticmethod
    def create_directory(dir_path):
        # Remove the directory if it already exists
        if os.path.exists(dir_path):
            try:
                # Remove the directory and its contents
                shutil.rmtree(dir_path)
            except Exception as e:
                print(f"Failed to remove '{dir_path}': {e}")

        # Create the directory
        try:
            os.makedirs(dir_path)
        except Exception as e:
            print(f"Failed to create '{dir_path}': {e}")       


    @staticmethod
    # Delete directory and its contents    
    def delete_directory(dir_path):
        try:
            shutil.rmtree(dir_path)
        except Exception as e:
            raise Exception(f"Failed to remove '{dir_path}': {e}")


    @staticmethod
    # Define a custom sorting key function to extract the numeric part of the filenames
    def extract_flag_and_image_numbers(filename):
        match = re.search(r'flag(\d+)_(\d+)', filename)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return x, y
        return 0, 0  # Default values if extraction fails    


    @staticmethod
    def copy_image(source_dir, target_dir, image_name, new_name):
        source_path = os.path.join(source_dir, image_name)
        target_path = os.path.join(target_dir, new_name)

        try:
            shutil.copy2(source_path, target_path)
        except Exception as e:
            print(f"Failed to copy image '{image_name}': {e}")

    colors_with_names = [
        ('red', (0, 0, 255)),
        ('green', (0, 255, 0)),
        ('cyan', (255, 255, 0)),
        ('magenta', (255, 0, 255)),
        ('white', (255, 255, 255)),
        ('black', (0, 0, 0)),
        ('purple', (128, 0, 128)),
        ('brown', (165, 42, 42)),
        ('pink', (255, 192, 203)),  
        ('lime', (0, 255, 0)),      
        ('teal', (0, 128, 128)),    
        ('gold', (255, 215, 0)),    
        ('silver', (192, 192, 192)),
        ('maroon', (128, 0, 0)),
        ('navy', (0, 0, 128)),
        ('indigo', (75, 0, 130)),
        ('darkgreen', (0, 100, 0)),
        ('olive', (128, 128, 0)),
        ('gray', (128, 128, 128)),
        ('lightgray', (211, 211, 211)),
        ('darkgray', (169, 169, 169)),
        ('slategray', (112, 128, 144)),
        ('coral', (255, 127, 80)),
        ('turquoise', (64, 224, 208)),
        ('violet', (238, 130, 238)),
        ('orchid', (218, 112, 214)),
        ('skyblue', (135, 206, 235)),        
        ]
    

    @staticmethod
    def draw_boxes(tracked_object, image_path, color, i):
        image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

        isIDWrited = False
        for box_details in tracked_object:
            # Calculating box1 width and height
            width = box_details['box']['x2'] - box_details['box']['x1']
            height = box_details['box']['y2'] - box_details['box']['y1']
            
            # Define box coordinates
            x1 = box_details['box']['x1']
            y1 = box_details['box']['y1']
            x2 = x1 + width
            y2 = y1 + height
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness = 2)

            # Add text with the number i
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1
            text_size = cv2.getTextSize(str(i), font, font_scale, font_thickness)[0]
            text_x = int(x1 + (width - text_size[0]) / 2)
            text_y = int(y1 - 5)
            if not isIDWrited:
                cv2.putText(image, str(i), (text_x, text_y), font, font_scale, color, font_thickness, cv2.LINE_AA)
                isIDWrited = True

        cv2.imwrite(image_path, image)

