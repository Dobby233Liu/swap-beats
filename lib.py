import pydub
import math
from tqdm.auto import tqdm, trange

BEATS = 4
CF_AMOUNT = 10
# As for now this seems to be a good choice.
# I'm battling this $4!7 during testing BIG SHOT
ROUNDING = math.floor

def get_song_seg(songdata):
    r = pydub.AudioSegment.from_file(songdata["fn"], songdata["ff"])
    if r.channels == 1:
        r = pydub.AudioSegment.from_mono_audiosegments(r, r)
    return r

def s_to_ms(n, rounding=ROUNDING):
    return rounding(n * 1000)

def each_beat_takes_seconds(bpm):
    return 60 / bpm

def arrange_like(origin, example, placeholder=None):
    assert(len(origin) == len(example))

    ret = []
    for i in example:
        ap = None
        if i <= 0 or i > len(origin):
            ap = placeholder
        else:
            ap = origin[i - 1]
        ret.append(ap)

    return ret

def normalize(seg):
    return seg.normalize().remove_dc_offset()

def _shuffle_beats(songdata, songseg, beats=BEATS):
    buf = songseg
    _temp_endbuf = None
    new_aud = pydub.AudioSegment.empty()

    rounding = ROUNDING
    if "rounding" in songdata:
        rounding = songdata["rounding"]
    assert(callable(rounding))
    log = tqdm.write # TODO: disable functionality
    # dont_show_progress = interactive and None or True

    beats = songdata.get("beats", BEATS)
    if "start" in songdata:
        new_aud.append(normalize(buf[:s_to_ms(songdata["start"], rounding=rounding)]), crossfade=0)
        buf = buf[s_to_ms(songdata["start"], rounding=rounding):]
    if "end" in songdata:
        _temp_endbuf = normalize(buf[-s_to_ms(songdata["end"], rounding=rounding):0])
        buf = buf[:-s_to_ms(songdata["end"], rounding=rounding)]
    tick = -1
    _back_pat_if_callable = None
    _call_pat_each_loop_end = False
    pat = [1, 4, 3, 2]
    if "new_order" in songdata:
        pat = songdata["new_order"]
    if callable(pat):
        _back_pat_if_callable = pat
        pat = _back_pat_if_callable(tick)
        if type(pat) is tuple:
            _call_pat_each_loop_end = pat[1]
            pat = pat[0]
    assert(len(pat) == beats)
    log("%d BPM, %d/Who cares" % (songdata["bpm"], beats))
    log("Swap pattern is " + str(pat))

    slice_portion = s_to_ms(each_beat_takes_seconds(songdata["bpm"]), rounding=rounding)
    if "beat_delay" in songdata:
        slice_portion = slice_portion + s_to_ms(songdata["beat_delay"], rounding=rounding)
    cf_amount = CF_AMOUNT
    if "crossfade" in songdata:
        cf_amount = songdata["crossfade"]
    log("One beat takes %dms" % slice_portion)
    log("Crossfade uses " + "%dms" % cf_amount)

    with tqdm(disable=None, leave=False) as pbar:
        while len(buf) > 0:
            segs = []
            pbar.set_description("Trimming beats")
            for beat in trange(beats, leave=False, disable=None):
                seg = buf[:slice_portion]
                buf = buf[slice_portion:]
                seg = normalize(seg)
                segs.append(seg)
                pbar.update(0)
            segs = arrange_like(segs, pat, placeholder=pydub.AudioSegment.empty())
            pbar.set_description("Appending beats")
            for parti in trange(len(segs), leave=False, disable=None):
                part = segs[parti]
                crossfade = cf_amount
                if (len(new_aud) < crossfade) or (len(part) < crossfade):
                    crossfade = 0
                new_aud = new_aud.append(part, crossfade=crossfade)
                pbar.update(0)
            pbar.set_description("...")
            if _back_pat_if_callable is not None and callable(_back_pat_if_callable) and _call_pat_each_loop_end:
                _old_pat = pat
                pat = _back_pat_if_callable(tick)
                if type(pat) is tuple:
                    pat = pat[0]
                assert(len(pat) == beats)
                if _old_pat != pat:
                    log("Pattern is now " + str(pat))
                pbar.update(0)
            tick = tick + 1
            pbar.update()

    if _temp_endbuf is not None:
        crossfade = cf_amount
        if len(new_aud) < crossfade:
            crossfade = 0
        new_aud = new_aud.append(_temp_endbuf, crossfade=crossfade)

    new_aud = normalize(new_aud)

    return new_aud

def shuffle_beats(songdata):
    songseg = get_song_seg(songdata)
    songseg = _shuffle_beats(songdata, songseg)
    return songseg

def shuffle_beats_and_export(songdata):
    out = shuffle_beats(songdata)
    fn = "shuffled_" + songdata["fn"]
    out.export(fn, format=songdata["ff"])
    return fn
