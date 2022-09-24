import re
import requests
import apiaudio 
from config import API_KEY, AUTH_TOKEN


### VIDEO2SUBTITLE SECTION 


def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data

def upload_file(filename):
    headers = {'authorization': AUTH_TOKEN}
    response = requests.post('https://api.assemblyai.com/v2/upload',
                            headers=headers,
                            data=read_file(filename))
    video_url = response.json()["upload_url"]
    return video_url


def send_to_assembly(filename):
    transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {
    "authorization": AUTH_TOKEN,
    "content-type": "application/json"
    }
    transcript_request = {
    "audio_url": upload_file(filename)
    }

    transcript_response = requests.post(transcript_endpoint, 
                                    json=transcript_request,
                                    headers=headers)


    transcript_id = transcript_response.json()['id']
    sub_endpoint = transcript_endpoint + "/" + transcript_id

    return headers, sub_endpoint



### APIAUDIO FOR TEXT2SPEECH SECTION

apiaudio.api_key = API_KEY


def is_time_stamp(l):
  if l[:2].isnumeric() and l[2] == ':':
    return True
  return False

def has_letters(line):
  if re.search('[a-zA-Z]', line):
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
  if l[0] == '(' and l[-1] == ')':
    return True
  if not has_letters(line):
    return True
  return False

def is_lowercase_letter_or_comma(letter):
  if letter.isalpha() and letter.lower() == letter:
    return True
  if letter == ',':
    return True
  return False

def clean_up(lines):

    new_lines = []
    for line in lines[1:]:
        if has_no_text(line):
            continue
        elif len(new_lines) and is_lowercase_letter_or_comma(line[0]):
            new_lines[-1] = new_lines[-1].strip() + ' ' + line
        else:
            new_lines.append(line)

    return new_lines


def send_to_audio(filename, speed=105):
    
    script = apiaudio.Script.create(
    scriptText=(
    f"""
    <<soundSegment::intro>><<sectionName::first>> {clean_up(filename)[0]}
    """), 
    scriptName="workinprogress")
    

    r = apiaudio.Speech.create(
    scriptId=script.get("scriptId"), 
    voice="liam",
    speed=speed
        )


    r = apiaudio.Mastering().create(
        scriptId=script.get("scriptId"),
        )
    
    file = apiaudio.Mastering.download(scriptId=script.get("scriptId"))
    print(file)