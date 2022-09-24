import requests
import argparse
import sys
from time import sleep
from utils import send_to_assembly, send_to_audio


def main(filename, speed, voice):
    print("Uploading the file ...")
    headers, sub_endpoint = send_to_assembly(filename)

    polling_response = requests.get(sub_endpoint, headers=headers)
    while polling_response.json()['status'] != 'completed':
        sleep(5)
        print("Transcript processing ...")
        try:
            polling_response = requests.get(sub_endpoint, headers=headers)
        except:
            print("Failed transcription")

    response_srt = requests.get(f"{sub_endpoint}/srt", headers=headers)

    subtitle = response_srt.text.split("\n")
    send_to_audio(subtitle, speed, voice)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Welcome to Dubbing AI")
    parser.add_argument("filename", help="video filename")
    parser.add_argument("--speed", type=int, help=("speed of the generated audio,"
                          "default is 105, which is the speed of a native speaker."))
    parser.add_argument("--voice", help="you can choose different voice from api audio list, default liam")
    
    args = parser.parse_args()
    
    main(args.filename, args.speed, args.voice)