import os


def time(now):
    slices = now.split(':')
    out = ''

    if len(slices[0]) == 1:
        out += '0' + slices[0]

    else:
        out += slices[0]

    out += ':'

    if len(slices[1]) == 1:
        out += '0' + slices[1]

    else:
        out += slices[1]

    return out


def temp():
    return int(float(os.popen('vcgencmd measure_temp').read()[5:-3]))
    