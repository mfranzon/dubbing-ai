import re
import sys
import requests
from pathlib import Path
import apiaudio
from moviepy.editor import VideoFileClip
from moviepy.editor import AudioFileClip
from moviepy.editor import CompositeAudioClip
from config import AUDIO_API_KEY, ASSEMBLY_AUTH_TOKEN


### VIDEO2SUBTITLE SECTION


def read_file(filename, chunk_size=5242880):
    with open(filename, "rb") as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data


def upload_file(filename, auth=ASSEMBLY_AUTH_TOKEN):
    if auth is None:
        raise ValueError("A token is required")
    headers = {"authorization": auth}
    if isinstance(filename, str):
        sys.stdout.flush()
        print(f"{filename} is passed")
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=read_file(filename),
        )
    else:
        sys.stdout.flush()
        print("Byte stream")
        response = requests.post(
            "https://api.assemblyai.com/v2/upload", headers=headers, data=filename
        )
    print(response.json())
    video_url = response.json()["upload_url"]
    return video_url


def send_to_assembly(filename, auth=ASSEMBLY_AUTH_TOKEN):
    if auth is None:
        raise ValueError("A token is required")
    transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {"authorization": auth, "content-type": "application/json"}
    transcript_request = {"audio_url": upload_file(filename, auth=auth)}

    transcript_response = requests.post(
        transcript_endpoint, json=transcript_request, headers=headers
    )

    transcript_id = transcript_response.json()["id"]
    sub_endpoint = transcript_endpoint + "/" + transcript_id

    return headers, sub_endpoint


### APIAUDIO FOR TEXT2SPEECH SECTION


def is_time_stamp(l):
    if l[:2].isnumeric() and l[2] == ":":
        return True
    return False


def has_letters(line):
    if re.search("[a-zA-Z]", line):
        return True
    return False


def has_no_text(line):
    l = line.strip()
    if not len(l):
        return True
    if l.isnumeric():
        return True
    if is_time_stamp(l):
        return True
    if l[0] == "(" and l[-1] == ")":
        return True
    if not has_letters(line):
        return True
    return False


def is_lowercase_letter_or_comma(letter):
    if letter.isalpha() and letter.lower() == letter:
        return True
    if letter == ",":
        return True
    return False


def clean_up(lines):

    new_lines = []
    for line in lines[1:]:
        if has_no_text(line):
            continue
        elif len(new_lines) and is_lowercase_letter_or_comma(line[0]):
            new_lines[-1] = new_lines[-1].strip() + " " + line
        else:
            new_lines.append(line)

    return new_lines


def dubbing(p_name, subtitle, video_name, speed=105, voice="liam", auth=AUDIO_API_KEY):
    if auth is None:
        raise ValueError("A token is required")
    apiaudio.api_key = auth

    script = apiaudio.Script.create(
        scriptText=(
            f"""
    <<soundSegment::intro>><<sectionName::first>> {clean_up(subtitle)[0]}
    """
        ),
        scriptName=f"{Path(p_name).stem.split('.')[0]}",
    )

    print(clean_up(subtitle))

    r = apiaudio.Speech.create(
        scriptId=script.get("scriptId"), voice=voice, speed=speed
    )

    r = apiaudio.Mastering().create(
        scriptId=script.get("scriptId"),
    )

    audio_file = apiaudio.Mastering.download(scriptId=script.get("scriptId"))
    print(audio_file)

    ### EDIT VIDEO ADDING THE NEW DUBBED FILE

    videoclip = VideoFileClip(f"{video_name}")
    new_clip = videoclip.without_audio()
    audioclip = AudioFileClip(f"{audio_file}")

    new_audioclip = CompositeAudioClip([audioclip])
    new_clip.audio = new_audioclip
    final_video = f"Dubbed_{Path(video_name).stem.split('.')[0]}.mp4"
    new_clip.write_videofile(final_video)
    return final_video
