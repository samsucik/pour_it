# sudo apt-get install swig pulseaudio libpulse-dev pyaudio
# pip install pocketsphinx
import os, pocketsphinx #, pyttsx
from pocketsphinx import LiveSpeech, get_model_path, AudioFile
from time import sleep
from pocketsphinx import AudioFile
import speech_recognition as sr

# remote python setup
# import rpyc
# conn = rpyc.classic.connect('ev3dev')
# ev3 = conn.modules['ev3dev.ev3']

class Speech():
    def __init__(self):
        # self.setup_tts()
        self.set_up_speech_recogniser()
        self.phrase_file_name = "phrase.raw"

        self.sphinx_model_path = os.path.join(get_model_path(), 'en-us')
        print(self.sphinx_model_path)

        self.drink_options = set({"WATER", "MEDICINE", "LEMONADE"})
        self.yes_no_options = set({"OK", "NO"})


    def set_up_speech_recogniser(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 600


    def record_phrase(self, fname="phrase.raw"):
        with sr.Microphone(device_index=0, sample_rate=16000) as source:
            audio = self.recognizer.listen(source)
            with open("phrase.raw", "wb") as f:
                f.write(audio.get_raw_data())
        print("...")


    # def setup_tts(self):
    #     self.tts_engine = pyttsx.init()
    #     rate = self.tts_engine.getProperty('rate')
    #     self.tts_engine.setProperty('rate', rate-50)
    #     self.tts_engine.setProperty('voice', 'english')


    def say(self, utterance):
        # l = len(utterance)
        # self.tts_engine.say(utterance)
        # self.tts_engine.runAndWait()
        print(utterance)
        # ev3.Sound.speak(utterance)


    def get_spoken_utterance(self):
        self.record_phrase(fname=self.phrase_file_name)
        # speech = LiveSpeech(
        #     # audio_device='hw:0',
        #     verbose=False,
        #     sampling_rate=16000,
        #     buffer_size=2048,
        #     no_search=False,
        #     full_utt=False,
        #     hmm=self.sphinx_model_path,
        #     dic='words.dic',
        #     lm='words.lm',
        #     kws='pour_it.list'
        # )

        speech = AudioFile(
            audio_file=self.phrase_file_name,
            verbose=False,
            # sampling_rate=16000,
            buffer_size=2048,
            no_search=False,
            full_utt=False,
            hmm=self.sphinx_model_path,
            dic='words.dic',
            lm='words.lm',
            kws='words.list'
        )
        words = set()
        for phrase in speech:
            with open("stats.txt", "a+") as f:
                f.write("\n" + str(phrase.segments(detailed=True)))
                print(phrase.segments(detailed=True))
            print("{} ({})".format(phrase, phrase.probability()))
            for word in str(phrase).split(' '):
                words.add(word.strip())
        if len(words) > 0:
            print("\nYou said: {}".format(' '.join(list(words))))

        return words


    def choose_one_from_list(self, words, options, allow_multiple=False):
        detected_options = set()
        for word in words:
            if word in options:
                detected_options.add(word)
        
        if len(detected_options) == 0:
            return None
        elif len(detected_options) == 1 or allow_multiple:
            return list(detected_options)[0]
        else:
            return None


    def greet_user(self):
        print("\nHello, dear friend! I am your intelligent assistant YARR.\n")


    def get_drink_option(self):
        utterance = None
        while True:
            self.say("What would you like to drink?")
            utterance = self.get_spoken_utterance()
            
            drink_option = self.choose_one_from_list(utterance, self.drink_options)
            if drink_option:
                while True:
                    self.say("You want {}, correct?".format(drink_option))
                    utterance = self.get_spoken_utterance()
                    yes_no_option = self.choose_one_from_list(utterance, self.yes_no_options)
                    if yes_no_option == "OK":
                        self.say("Perfect, I will give you some {}.".format(drink_option))
                        return drink_option
                    elif yes_no_option == "NO":
                        self.say("Oh, I see.")
                        break
                    else:
                        self.say("Sorry, I didn't understand.")
            else:
                self.say("Sorry, which drink do you want?")


speech = Speech()
speech.greet_user()
while True:
    drink_option = speech.get_drink_option()
# print("\nUSER WANTS: {}".format(drink_option))