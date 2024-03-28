import time
import argparse
import DahuaCameraCommunication

## need to first define which camera you want to work with: south or north

location = "south"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='GetCameraStatus',
                    description='The script fetch the camera PTZ values in loop till user stop it')
    
    parser.add_argument('-s', '--sleep', default=15, help='Sleep duration in seconds')

    args = parser.parse_args()

    print(f'Start fetching PTZ values each {args.sleep}')
    with open('PTZCamValues.txt', 'a') as file:
        iteration = 23
        # Looping till user intrerrupt
        while True:
            print (iteration)
            (zoom, tilt, pan) = DahuaCameraCommunication.getPTZValues(location)
            # Write ptz values into file
            file.write(f'#{iteration} - {zoom} , {tilt}, {pan}\n')
            iteration += 1
            time.sleep(args.sleep)