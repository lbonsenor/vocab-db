import re
import pykakasi

def decompose_syllable(input):
    BASE = 0xAC00
    LAST = 0XD7A3
    MEDIAL_COUNT = 21
    FINAL_COUNT = 28

    unicode = ord(input)
    
    if unicode < BASE or unicode > LAST:
        return (input if unicode < 128 else None)

    initials = ["g", "kk", "n", "d", "tt", "r", "m", "b", 
                "bb", "s", "ss", "", "j", "jj", "ch", "k", 
                "t", "p", "h"]

    medials = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", 
               "o", "wa", "wae", "oe", "yo", "u", "wo", "we", 
               "wi", "yu", "eu", "ui", "i"]

    finals = ["", "k", "kk", "ks", "n", "nj", "nh", "t", 
              "l", "lk", "lm", "lb", "ls", "lt", "lp", "lh", 
              "m", "b", "ps", "s", "ss", "ng", "j", "ch", 
              "k", "t", "p", "h"]
    
    offset = unicode - BASE

    i_index = offset // (MEDIAL_COUNT * FINAL_COUNT)
    m_index = (offset % (MEDIAL_COUNT * FINAL_COUNT)) // FINAL_COUNT
    f_index = offset % FINAL_COUNT

    return initials[i_index] + medials[m_index] + finals[f_index]

def hangul(input):
    output = []

    for char in input:
        romanized = decompose_syllable(char)
        if romanized is not None:
            output.append(romanized)
    
    return ''.join(output)

def romanize(text):
    if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', text):  # Japanese
        kks = pykakasi.kakasi()
        result = kks.convert(text)
        return " ".join([item['hepburn'] for item in result])
    elif re.search(r'[\uac00-\ud7a3]', text):  # Korean
        return hangul(text)
    else:
        return text