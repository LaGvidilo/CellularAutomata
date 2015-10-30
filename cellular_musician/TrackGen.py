import random
import math

from mingus import containers

from mingus.containers import Bar, Note, MidiInstrument

from cellular_musician.ElementaryCAEngine import Engine
from cellular_musician.ElementaryCAEngine import EdgeType


class Track(object):
    """
        A track generating class. Possible name change due to conflict with mingus.containers.track.
        Future goal is to wrap all mingus needed so user can easily modify songs without having to dive into midi.
    """
    initial = []
    instrument_nr = 0
    track = None

    def __init__(self, initial=[]):
        self.initial = initial
        self.track = containers.Track()

    def set_instrument(self, number):
        instr = MidiInstrument()
        instr.instrument_nr = number
        self.track.instrument = instr
        return instr

    def generate(self, length, bars, octave, scale=["C", "D", "E", "G", "A"], instrument=1, rand_length=False,
                 time_signature=(4, 4), velocity=[64, 64], channel=1, rests=True):
        # create the instrument for the main track
        instr = MidiInstrument()
        instr.instrument_nr = instrument  # MIDI instrument number: http://www.midi.org/techspecs/gm1sound.php
        track = containers.Track(instr)
        self.set_instrument(instrument)
        if not self.initial:
            self.initial = [False] * 9
            print "Error: initial set empty. Defaulting..."
        rule_number = 30
        if rand_length:  # start with quarter note as base
            length = 4

        automata = Engine(rule_number, init_row=self.initial, edge_type=EdgeType.LOOP)

        # Index counting for diagnostics
        counts = dict((n, 0) for n in range(0, len(scale) * 2))
        index = 5  # starting value
        for b in range(0, (length * bars) / 4):
            bar = Bar("C", time_signature)
            while bar.space_left() != 0:  # runs until we're out of space for notes (e.g. complete bar)
                automata.step()  # take a step
                i = automata.rows[-1]
                index = (index + int(round(median([ind for ind in range(0, len(i)) if i[ind] == True]),
                                           0))) // 2  # average last value with this one and use as index
                if rand_length:  # if we're randomly generating lengths of notes
                    length = int(math.pow(2, random.randint(1, 4)))
                    left = bar.space_left()
                    space = ((left - (left % 0.25)) * 16) if left > 0.25 else left * 16
                    if space < 16 / length:
                        length = int(16.0 / space)
                if rests and random.randint(0, 20) == 1:  # same rest generation
                    bar.place_rest(16)
                    continue  # skip the rest
                # strip off the top note for the melody
                name = list(scale)[index if index < 5 else index - 4]  # can be used for diagnostics
                counts[index] += 1
                n = Note(name,
                         octave=octave if index < 5 else octave + 1)
                n.set_velocity(random.randint(velocity[0], velocity[1]))  # random velocity, can feel more "real"
                n.set_channel(channel) # if we want > 1 instruments we need > 1 channel
                bar.place_notes(n, length)
            track.add_bar(bar)  # add bar to track
        self.track = track  # set our track object to the newly generated track
        for n in counts:
            print str(n) + ": " + str(counts[n])  # diagnostics
        print "======="
        return self

    # DEPRECATED, JUST FOR REFERENCE
    def random_generate(self, bars, octave, time_signature=(4, 4), velocity=[64, 64]):
        # Generates track in random key with random note lengths
        scale = Util().major_penta(Util().notes[random.randint(0, len(Util().notes))])
        length = 8
        # create the instrument for the main track
        instr = MidiInstrument()
        instr.instrument_nr = random.randint(1,
                                             104)  # MIDI instrument number: http://www.midi.org/techspecs/gm1sound.php
        track = containers.Track(instr)
        self.initial = [False] * 9
        self.initial[random.randint(0, 8)] = True
        rule_number = 30
        automata = Engine(rule_number, init_row=self.initial, edge_type=EdgeType.LOOP)
        for b in range(0, bars):
            bar = Bar("C", time_signature)
            while bar.space_left() != 0:
                automata.step()

                i = automata.rows[-1]
                length = int(math.pow(2, random.randint(0, 4)))
                if length > 16:
                    print length
                for index, d in enumerate(i):
                    left = bar.space_left()
                    space = ((left - (left % 0.25)) * 16) if left > 0.25 else left * 16
                    if space < 16 / length:
                        length = int(16.0 / space)
                    if d and random.randint(0, 20) == 1:
                        bar.place_rest(length)
                        break
                    if index > 0 and d:
                        # strip off the top note for the melody
                        n = Note(list(reversed(scale))[index if index < 5 else index - 4],
                                 octave=octave if index < 5 else octave + 1)
                        n.set_velocity(random.randint(velocity[0], velocity[1]))
                        bar.place_notes(n, length)
                        break
                print Track.format_block(i)
            track.add_bar(bar)
        self.track = track
        return self

    @staticmethod
    def format_block(i1):
        return "|" + "".join([u'?' if n1 else u"  " for n1 in i1]) + "|"


class Util(object):
    notes = ['a', 'a#', 'b', 'c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#'] * 2
    notes = [note.upper() for note in notes]

    def chroma(self, x):
        return [i for i in self.notes[self.notes.index(x):] + self.notes[:self.notes.index(x)]] + [x]

    def major(self, x):
        return (self.chroma(x)[:5] + [self.chroma(x)[5]] + self.chroma(x)[5:12])[::2] + [x]

    def major_penta(self, x):
        return [i for idx, i in enumerate(self.major(x)) if idx not in (3, 6)]

    def minor_penta(self, x):
        return (self.major_penta(self.notes[self.notes.index(x) + 3])[:-1] * 2)[-6:]


def median(lst):
    lst = sorted(lst)
    if len(lst) < 1:
        return None
    if len(lst) % 2 == 1:
        return lst[((len(lst) + 1) / 2) - 1]
    else:
        return float(sum(lst[(len(lst) / 2) - 1:(len(lst) / 2) + 1])) / 2.0