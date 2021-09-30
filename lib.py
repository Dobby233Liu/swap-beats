import pydub
import random

BEATS = 4

def get_random_beat_pattern():
    ret = list(range(BEATS))
    random.shuffle(ret)
    return ret

def get_song_seg(songdata):
    return pydub.AudioSegment.from_file(songdata["fn"], songdata["ff"])

def s_to_ms(n):
    return n * 1000

def each_beat_takes_seconds(bpm):
    return bpm / 60

def arrange_like(origin, example):
    if len(origin) != len(example):
        raise Exception("no")
    ret = []
    for i in range(len(origin)):
        if i == example[i]:
            ret.append(origin[i])
    if len(ret) != len(origin):
        raise IndexError("what")
    return ret

def shuffle_beats(songdata):
    origin_seg = get_song_seg(songdata)
    new_seg = pydub.AudioSegment.empty()

    pat = get_random_beat_pattern()
    slicing_portion = s_to_ms(each_beat_takes_seconds(songdata["bpm"]))
    rest_ms = len(origin_seg)
    seek = 0

    while rest_ms > 0:
        segs = []
        for i in range(BEATS):
            start_seek = seek
            seek = seek + slicing_portion
            if seek > rest_ms: # what no clamp does to mfers
                seek = rest_ms
            rest_ms = rest_ms - slicing_portion
            segs.append(origin_seg[start_seek:seek])
        segs = arrange_like(segs, pat)
        for i in segs:
            new_seg.append(i)

    return new_seg

def make_lemonade(songdata):
    fn = "shuffled_" + songdata["fn"] + ".wav"
    shuffle_beats(songdata).export(fn, format="wav")
    return fn
