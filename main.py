import streamlit as st

# Configure the Streamlit  front page
st.set_page_config(
    page_title="Personal Voice Assistant",
    page_icon=":microphone:",
    layout="centered"
    )

# import other necessary libraries
import os        # to get path of the .env file
import time      # to set time for listen
import pyttsx3   # convert text to speech
import speech_recognition as sr  # to convert speech to text
from groq import Groq  # API key to use LLM service
from dotenv import load_dotenv  # to load API key from sysytem

# load the API key inside code
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# checking if API key is set or not
if not GROQ_API_KEY:
    st.error("Missing API Key")
    st.stop()

# configure the LLM
client = Groq(api_key = GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# iNitialize speech to text recognizer
recognizer = sr.Recognizer()

# Initializze text to speech engine
def get_tts_engine():
    try:
        engine = pyttsx3.init()    
        return engine
    except Exception as e:
        st.error("Failed to initialize text-to-speech engine")
        return None
    
def listen_to_speech():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration = 1) 
            audio = recognizer.listen(source, phrase_time_limit = 10)

        text = recognizer.recognize_google(audio)
        return text.lower()
    except sr.UnknownValueError:
        return "Sorry, I don't catch you"
    except sr.RequestError as e:
        return "Speech service not available"
    except Exception as e:
        return f"ERROR: {e}"

# send the request to llm with the help of GROQ API key
def get_ai_response(messages):
    try:
        response = client.chat.completions.create(
            model = MODEL,
            messages = messages,
            max_tokens = 100,
            temperature = 0.7
        )

        # out of many responses by llm we are taking 0th response
        result = response.choices[0].message.content.strip()
        return result.strip() if result else "Sorry, I couldn't generate a response."
    except Exception as e:
        return f"Error getting AI response: {e}"
    
def speak(text, voice_gender = "Girl"):
    try:
        engine = get_tts_engine()
        if engine is None:
            return
    
        # get the list of available voices
        voices = engine.getProperty("voices")

        if voices:
            if voice_gender == "Boy":
                for voice in voices:
                    if "male" in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break
            else:
                # set the girl voice
                for voice in voices:
                    if "male" in voice.name.lower() or "zira" in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break
        engine.setProperty("rate", 200)  # speed of speech
        engine.setProperty("volume", 0.8)    # volume of speech
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        st.error(f"TTS Error {e}")
    
def main():
    st.title("Personal Voice Assistant")
    st.markdown("---")

    # initialize session state for chatting
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "You are a helpful voice assistant. Reply just one line"}
        ]

    # initialize the session messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    with st.sidebar:
        st.header("Controls")
        
        tts_enabled = st.checkbox("Enable Text-to-Speech", value=True)

        # voice selection
        voice_gender = st.selectbox(
            "Voice Gender",
            options=["Girl", "Boy"],
            index = 0,
            help = "Choosbe Voice Type"
        )

        if st.button("Start Voice Input", type = "primary", use_container_width = True):
            with st.spinner("Listening..."):
                user_input =  listen_to_speech()
                # user_input is not empty and don't get error then if statement will execute
                if user_input and user_input not in["Sorry, I don't catch you", "Speech service not available"]:
                    # storing user message in messages[], so that we can display on screen
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "assistant", "content": user_input})

                    # get response from LLM
                    with st.spinner("Thinking..."):
                        ai_response = get_ai_response(st.session_state.chat_history)
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

                    # speak the ai reply
                    if tts_enabled:
                        speak(ai_response, voice_gender)

                    # refresh the display
                    st.rerun()

        st.markdown("---")

        # code to recive text input rather than voice input
        st.subheader("Text Input")
        user_text = st.text_input("Type your message here", key = "text_input")
        if st.button("Send Text", type="primary", use_container_width=True) and user_text:
            st.session_state.messages.append({"role": "user", "content": user_text})
            st.session_state.chat_history.append({"role": "assistant", "content": user_text})

            with st.spinner("Thinking..."):
                ai_response = get_ai_response(st.session_state.chat_history)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

            # speak the ai reply
            if tts_enabled:
                speak(ai_response, voice_gender)

            # refresh the display
            st.rerun()

        st.markdown("---")

        # button to clear our chat history
        if st.button("Clear Chat History", type = "secondary", use_container_width = True):
            st.session_state.messages = []
            st.session_state.chat_history = [
                {"role": "system", "content": "You are a helpful voice assistant. Reply just one line"}
            ]
            st.rerun()
    
    # display conversation on right side
    st.subheader("Conversation")

    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

    # Starting message
    if not st.session_state.messages:
        st.info("Welcome: Click on voice input button to start")


if __name__ == "__main__":
    main()
    