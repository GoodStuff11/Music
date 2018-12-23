import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import wave
from multiprocessing import Process


class Audio:
    def __init__(self):
        pass

    @staticmethod
    def frequency_to_note(f, a4=440):
        letters = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        n = round(12 * np.log(2 ** (3 / 4) * f / a4, 2))
        note = int(n % 12)
        octave = int(n // 12) + 4
        return letters[note] + str(octave)

    @staticmethod
    def note_to_frequency(note, a4=440):
        """
        :param note: Note letter string, lowercase letter and # for sharp and b for flat
        :param a4: frequency of a4 in Hz
        :return: frequency of note given
        """
        # # as sharp and b as flat
        letters = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        letters2 = ['c', 'db', 'd', 'eb', 'e', 'f', 'gb', 'g', 'ab', 'a', 'bb', 'b']
        if note[:-1] in letters:
            n = letters.index(note[:-1]) + 12 * (int(note[-1]) - 4)
        elif note[:-1] in letters2:
            n = letters2.index(note[:-1]) + 12 * (int(note[-1]) - 4)
        f = a4 * 2 ** (n / 12 - 3 / 4)
        return f


class PlayAudio(Audio):
    def __init__(self, file: str):
        Audio.__init__(self)
        self.file = file
        self.run_parallel(self.play, self.disp)

    @staticmethod
    def run_parallel(*fns):
        proc = []
        for fn in fns:
            p = Process(target=fn)
            p.start()
            proc.append(p)
        for p in proc:
            p.join()

    def play(self):
        f = wave.open(self.file, "rb")
        chunk = 1024
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        data = f.readframes(chunk)
        # play stream
        while data:
            stream.write(data)
            data = f.readframes(chunk)

    def disp(self):
        data, sample_rate = sf.read(self.file)
        plt.plot([x / sample_rate for x in range(len(data))], data)
        plt.show()

    def modify(self):
        data, sample_rate = sf.read(self.file)
        sf.write('new_file.wav', data, sample_rate)


class ModifyAudio(Audio):
    def __init__(self, new_file):
        Audio.__init__(self)
        self.file = new_file
        self.modify()

    def modify(self):
        data, sample_rate = sf.read(self.file)
        sf.write(self.file, data, sample_rate)


class GenerateAudio(Audio):
    def __init__(self, new_file, tempo, sample_rate):

        self.tempo = tempo
        self.sample_rate = sample_rate
        self.file = new_file
        self.parts = []

    def add_part(self):
        a = GeneratePart(self.tempo, self.sample_rate)
        self.parts.append(a)
        return a

    def write(self):
        m = min([len(p.data) for p in self.parts])  # minimum length of the arrays
        all_data = sum([np.array(p.data)[:m] for p in self.parts])  # set each of the data arrays to be the same length
        sf.write(self.file, all_data, self.sample_rate)


class GeneratePart(Audio):
    def __init__(self, tempo, sample_rate):
        Audio.__init__(self)

        self.data = []

        self.tempo = tempo
        self.sample_rate = sample_rate

        self.synth = self.sine
        self.vibrato_rate = 0
        self.vibrato_amplitude = 0

        self.current_dynamics = 0
        self.final_dynamics = 0
        self.dynamics_rate = 0

    @staticmethod
    def square(t):
        t = t % 1
        if t < 0.5:
            return 1
        else:
            return -1

    @staticmethod
    def triangle(t):
        t = t % 1
        if t <= 0.25:
            return 4 * t
        elif 0.25 < t <= 0.75:
            return 1 - 4 * (t - 0.25)
        elif 0.75 < t <= 1:
            return -1 + 4 * (t - 0.75)

    @staticmethod
    def sawtooth(t):
        t = t % 1
        return 2 * t - 1

    @staticmethod
    def sine(t):
        return np.sin(2 * np.pi * t)

    def set_synth(self, synth):
        if synth == 'square':
            self.synth = self.square
        elif synth == 'sawtooth':
            self.synth = self.sawtooth
        elif synth == 'sine':
            self.synth = self.sine
        elif synth == 'triangle':
            self.synth = self.triangle

    def set_dynamics(self, *dynamics):
        """
        :param dynamics: initial dynamics, final dynamics, beats of change
        :return: None
        """

        self.current_dynamics = dynamics[0]
        try:

            self.final_dynamics = dynamics[1]
            self.dynamics_rate = (dynamics[1] - dynamics[0])/dynamics[2]
            print(self.dynamics_rate)
        except IndexError:
            self.final_dynamics = dynamics[0]
            self.dynamics_rate = 0

    def set_vibrato(self, rate, amplitude):
        self.vibrato_rate = rate
        self.vibrato_amplitude = amplitude

    def add_rest(self, beats):
        current = self.current_dynamics

        self.set_dynamics(0)
        self.data += self.generate_note('a4', 60 * beats / self.tempo)
        self.set_dynamics(current)

    def add_note(self, note, beats):
        self.data += self.generate_note(note, 60 * beats / self.tempo)

    def generate_note(self, note, duration):
        # duration is seconds of note
        # t = 1 is one period

        f = self.note_to_frequency(note)

        def sign(x):
            if x > 0:
                return 1
            if x < 0:
                return -1
            return 0

        data = [0] * int(duration * self.sample_rate)
        for t in range(int(duration * self.sample_rate)):
            data[t] = int(self.current_dynamics * 2147483647 * self.synth(f * (t + self.vibrato_amplitude * np.sin(2 * np.pi * t * self.vibrato_rate / self.sample_rate)) / self.sample_rate))
            # dynamics - dynamics_f < 0 if crescendo
            if (self.current_dynamics - self.final_dynamics) * sign(self.dynamics_rate) < 0:
                self.current_dynamics += self.dynamics_rate * self.tempo / (60 * self.sample_rate)
        return data
