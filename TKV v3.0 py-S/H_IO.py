# H_io

cpillin  = []
cpillout = []
event = None

def set(event_):
    global event
    event = event_

def read_port():
    global cpillout
    if cpillout:
        return cpillout.pop(0)
    return -1

def write_port(val):
    global cpillin
    cpillin.append(val)

def clock():
    global cpillin, cpillout
    code, msg = event() or (0, None)
    if code == -1:
        return (2, msg)
    return (0, None)