import requests
from time import sleep
from utils import send_to_assembly
from utils import dubbing
from utils import create_zip
import streamlit as st

with st.sidebar:
    tk_assembly = st.text_input("TOKEN ASSEMBLY AI", type="password")
    tk_api_audio = st.text_input("TOKEN API AUDIO", type="password")
    speed = st.slider("Select the voice speed", 0, 130, 25)
    voice = st.selectbox("Which voice you want?", ("liam", "sonia", "aria", "ryan"))


st.title(
    """ Dubbing AI
End-to-end dubbing video system.
"""
)

p_name = st.text_input("Insert a name for this Project")

uploaded_file = st.file_uploader("Choose a video")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    
    with open(f'{uploaded_file.name}', 'wb') as wfile:
      wfile.write(bytes_data)

    st.video(bytes_data)

if st.button("Dubbing"):
    with st.spinner("Waiting for subtitle generation..."):
        headers, sub_endpoint = send_to_assembly(bytes_data, auth=tk_assembly)
        polling_response = requests.get(sub_endpoint, headers=headers)

        while polling_response.json()["status"] != "completed":
            sleep(5)
            print("Transcript processing ...")
            try:
                polling_response = requests.get(sub_endpoint, headers=headers)
            except:
                print("Failed transcription")

    st.success("Subtitle generated, now I am dubbing your video")
    response_srt = requests.get(f"{sub_endpoint}/srt", headers=headers)

    subtitle = response_srt.text.split("\n")

    with open(f"{p_name}.srt", "w") as _file:
        _file.write(response_srt.text)

    with st.spinner("Waiting for dubbing..."):
        final_video, audio_file = dubbing(
            p_name,
            subtitle,
            uploaded_file.name,
            speed=speed,
            voice=voice,
            auth=tk_api_audio,
        )

    video_file = open(f"{final_video}", "rb")
    video_bytes = video_file.read()
    st.success("Your video is ready!")
    st.video(video_bytes)

    create_zip(p_name, f'{p_name}.srt',
                              final_video, audio_file)
 
    st.write("Click here to download the generated files")
    with open(f"{p_name}.zip", "rb") as fp:
        btn = st.download_button(
            label="Download ZIP",
            data=fp,
            file_name="mydubbedvideo.zip",
            mime="application/zip"
        )