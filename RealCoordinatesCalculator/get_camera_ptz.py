import time
import argparse
import DahuaCameraCommunication

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='GetCameraStatus',
                    description='The script fetch the camera PTZ values in loop till user stop it')
    
    parser.add_argument('-s', '--sleep', default=15, help='Sleep duration in seconds')

    args = parser.parse_args()

    print(f'Start fetching PTZ values each {args.sleep}')
    iteration = 0
    with open('PTZCamValues.txt', 'a') as file:
        while True:
            (zoom, tilt, pan) = DahuaCameraCommunication.getPTZValues()
            print(f'Current PTZ values - ({zoom}, {tilt}, {pan})')
            # Write ptz values into file
            file.write(f'#{iteration} - {zoom} , {tilt}, {pan}\n')
            time.sleep(int(args.sleep))
            iteration =+ 1