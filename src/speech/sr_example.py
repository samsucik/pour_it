#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr

mic_index = -1
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
    if name.startswith("USB Device"):
        mic_index = index

mic_index = 0
print("Microphone device index: {}".format(mic_index))

# obtain audio from the microphone
r = sr.Recognizer()

# with sr.WavFile("test.wav") as source:
#     audio = r.record(source)

drinks = ["water", "medicine", "juice"]
yes_no = ["yes", "no"]
dictionary = [(word, 0.9) for word in drinks] + [(word, 0.999) for word in yes_no]
print(dictionary)

with sr.Microphone(device_index=mic_index, sample_rate=16000) as source:
    print("Be quiet!")
    r.adjust_for_ambient_noise(source)
    print("You can be noisy again :-)")

    while True:
        print("Say something!")
        audio = r.listen(source)

        try:
            print("Now recognising")
            phrase = r.recognize_sphinx(audio, keyword_entries=dictionary)
            print("Sphinx thinks you said : '{}'".format(phrase))
        except sr.UnknownValueError:
            print("Sphinx could not understand audio")
        except sr.RequestError as e:
            print("Sphinx error; {0}".format(e))