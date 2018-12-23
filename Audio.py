import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import wave
from multiprocessing import Process, freeze_support
import struct
import datetime as dt


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
    def __init__(self, new_file):
        Audio.__init__(self)

        self.tempo = 152
        self.sample_rate = 44100

        pp = 0.05
        p = 0.1
        mp = 0.15
        mf = 0.2
        f = 0.3

        def wait(bars):
            return [['dynamics', bars, 0, 0], ['a4', bars]]

        info1 = []
        info2 = []
        info3 = []

        def notes2112(note):
            return [[note, 1],
                    [note, 0.5],
                    [note, 0.5],
                    [note, 1]]

        chorus = [['bb5', 1],
                  ['a5', 0.5],
                  ['bb5', 0.5],
                  ['g5', 1]]
        upper_chorus = [['d6', 1],
                        ['c6', 0.5],
                        ['d6', 0.5],
                        ['bb5', 1]]
        g_scale = [['g5', 3],
                   ['f5', 3],
                   ['eb5', 3],
                   ['d5', 3]]
        e_scale = [['eb5', 3],
                   ['d5', 3],
                   ['c5', 3],
                   ['g4', 3]]
        # 1
        info1 += [['vibrato', 5, 5]]
        info1 += [['synth', 'sawtooth']]
        info1 += [['dynamics', 3 * 2, mf, mf]]
        info1 += 2 * chorus
        info1 += [['dynamics', 3 * 2, pp, pp]]
        info1 += 6 * chorus
        info1 += [['dynamics', 3 * 4, p, p]]
        info1 += 4 * chorus
        info1 += [['dynamics', 3 * 4, mp, mp]]
        info1 += 4 * chorus
        info1 += [['dynamics', 3 * 4, mf, f]]
        info1 += 4 * upper_chorus
        # 21

        # --------------------------------
        info2 += wait(3 * 4)
        info2 += [['vibrato', 5, 5]]
        info2 += [['synth', 'triangle']]
        info2 += [['dynamics', 3 * 4, pp, pp]]
        info2 += g_scale

        info2 += [['dynamics', 3 * 4, p, p]]
        info2 += g_scale
        info2 += [['dynamics', 3 * 4, mp, mp]]
        for i in ['c5', 'd5', 'eb5', 'd5']:
            info2 += notes2112(i)
        info2 += [['dynamics', 3 * 4, mf, f]]
        info2 += 4 * chorus
        # -------------------------------
        info3 += wait(3 * 8)
        info3 += [['vibrato', 5, 5]]
        info3 += [['synth', 'triangle']]
        info3 += [['dynamics', 3 * 4, p, p]]
        info3 += e_scale
        info3 += [['dynamics', 3 * 4, mp, mp]]
        for i in ['eb4', 'g4', 'c5', 'g4']:
            info3 += notes2112(i)
        info3 += [['dynamics', 3 * 4, mf, f]]
        info3 += [['d5', 3],
                  ['e5', 3],
                  ['f5', 1],
                  ['eb5', 1],
                  ['d5', 1],
                  ['g5', 0.5],
                  ['f5', 0.5],
                  ['eb5', 1],
                  ['d5', 1]]
        # ------------------------------

        data1 = self.generate_part(info1)
        data2 = self.generate_part(info2)
        data3 = self.generate_part(info3)

        length = min([len(data1), len(data2), len(data3)])
        data = np.array(data1)[:length] + np.array(data2)[:length] + np.array(data3)[:length]

        sf.write(new_file, data, self.sample_rate)

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

    def generate_part(self, notes_info):
        # notes_info = [[letter, notevalue], ... ]
        # or ['dynamics',beats,amp_i,amp_f]
        # or ['synth',synth_name]
        # notevalue : # notes/beat

        self.synth = self.sine
        self.vibrato = [0, 0]  # rate, amplitude
        self.dynamics = [0, 0, 0]  # current, end, rate

        data = []
        for note in notes_info:
            if note[0] == 'dynamics':
                # allow for [['dynamics',dynamics]]
                try:
                    self.dynamics[2] = (note[3] - note[2]) / note[1]
                    self.dynamics[0] = note[2]
                    self.dynamics[1] = note[3]
                except IndexError:
                    self.dynamics[2] = 0
                    self.dynamics[0] = note[1]
                    self.dynamics[1] = note[1]

            elif note[0] == 'synth':
                if note[1] == 'square':
                    self.synth = self.square
                elif note[1] == 'sawtooth':
                    self.synth = self.sawtooth
                elif note[1] == 'sine':
                    self.synth = self.sine
                elif note[1] == 'triangle':
                    self.synth = self.triangle
            elif note[0] == 'vibrato':
                self.vibrato = note[1:]
            else:
                data += self.generate_note(note[0], 60 * note[1] / self.tempo)
        return data

    def generate_note(self, note, T):
        # T is seconds of note
        # t = 1 is one period

        f = self.note_to_frequency(note)

        def sign(x):
            if x > 0:
                return 1
            if x < 0:
                return -1
            return 0

        data = [0] * int(T * self.sample_rate)
        for t in range(int(T * self.sample_rate)):
            data[t] = int(self.dynamics[0] * 2147483647 * self.synth(f * (t + self.vibrato[1] * np.sin(2 * np.pi * t * self.vibrato[0] / self.sample_rate)) / self.sample_rate))
            # dynamics - dynamics_f < 0 if crescendo
            if (self.dynamics[0] - self.dynamics[1]) * sign(self.dynamics[2]) < 0:
                self.dynamics[0] += self.dynamics[2] * self.tempo / (60 * self.sample_rate)
        return data


if __name__ == '__main__':
    freeze_support()  # required for multiprocessing
    GenerateAudio('audio.wav')
    PlayAudio('audio.wav')
