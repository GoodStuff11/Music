import ReadAudio2
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()  # required for multiprocessing

    tracks = ReadAudio2.GenerateAudio('Carol-of-the-Bells.wav', 152, 44100)
    part1 = tracks.add_part()
    part2 = tracks.add_part()

    pp = 0.05
    p = 0.1
    mp = 0.15
    mf = 0.2
    f = 0.3

    # -------------------------
    part1.set_dynamics(mf)
    part1.set_vibrato(5, 5)
    part1.set_synth('sawtooth')
    for i in range(16):
        if i == 2:
            part1.set_dynamics(pp)
        elif i == 8:
            part1.set_dynamics(p)
        elif i == 12:
            part1.set_dynamics(mp)

        part1.add_note('bb5', 1)
        part1.add_note('a5', 0.5)
        part1.add_note('bb5', 0.5)
        part1.add_note('g5', 1)

    # ------------------------
    part2.set_dynamics(pp)
    part2.set_vibrato(5, 5)
    part2.set_synth('triangle')
    part2.add_rest(3 * 4)
    for i in range(2):
        if i == 1:
            part2.set_dynamics(p)
        part2.add_note('g5', 3)
        part2.add_note('f5', 3)
        part2.add_note('eb5', 3)
        part2.add_note('d5', 3)

    tracks.write()
    ReadAudio2.PlayAudio('Carol-of-the-Bells.wav')
