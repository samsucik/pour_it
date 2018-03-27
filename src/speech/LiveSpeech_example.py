# sudo apt-get install swig pulseaudio libpulse-dev pyaudio
# pip install pocketsphinx
import os #, pyttsx
from pocketsphinx import LiveSpeech, get_model_path
from time import sleep

# remote python setup
import rpyc
conn = rpyc.classic.connect('ev3dev')
ev3 = conn.modules['ev3dev.ev3']

class Speech():
    def __init__(self):
        # self.setup_tts()
        self.sphinx_model_path = os.path.join(get_model_path(), 'en-us')

    def setup_tts(self):
        self.tts_engine = pyttsx.init()
        rate = self.tts_engine.getProperty('rate')
        self.tts_engine.setProperty('rate', rate-50)
        self.tts_engine.setProperty('voice', 'english')

    def say(self, utterance):
        l = len(utterance)
        # self.tts_engine.say(utterance)
        # self.tts_engine.runAndWait()
        print(utterance)
        ev3.Sound.speak(utterance)

    def get_spoken_utterance(self):
        speech = LiveSpeech(
            verbose=False,
            sampling_rate=16000,
            buffer_size=2048,
            no_search=False,
            full_utt=False,
            hmm=self.sphinx_model_path,
            dic='pour_it.dict',
            kws='pour_it.list'
        )

        for phrase in speech:
            # print("{} ({})".format(phrase, phrase.probability()))
            return str(phrase)

drink_options = set({"iron brew", "water", "medicine", "juice"})
yes_no = set({"yes", "no"})
speech = Speech()

def get_drink_option():
    utterance = None
    while True:
        speech.say("What would you like to drink?")
        utterance = speech.get_spoken_utterance()
        if utterance in drink_options:
            drink = utterance
            while True:
                speech.say("You want {}, correct?".format(drink))
                utterance = speech.get_spoken_utterance()
                if utterance == "yes":
                    speech.say("Perfect, I will give you some {}.".format(drink))
                    return drink
                elif utterance == "no":
                    speech.say("Oh, I see.")
                    break
                else:
                    speech.say("Sorry, I didn't understand.")
        else:
            speech.say("Sorry, I didn't catch that.")


drink = get_drink_option()
print("\nUSER WANTS: {}".format(drink))