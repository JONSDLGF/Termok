# H_gpu

cpillin  = []
cpillout = []
render = None

def set(render_):
    global render
    render = render_

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
    cpillin  = []
    cpillout = []
    call = [
        [0, [10, 10, [255, 0, 0]]],           # Pixel rojo
        [1, [20, 20, 15, 15, [0, 255, 0]]],   # Rectángulo verde
    ]
    render(call)
    return (0, None)