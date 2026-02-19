# M_Gin

import sdl2
import sdl2.ext
import numpy as np
try:
    import cupy as cp
except:
    pass

w, h, title = None, None, None
vmem:np = None
renderer, texture, window = None, None, None
initinstance = False

def start(w_,h_,title_):
    global initinstance, w, h, title
    initinstance=True
    w=w_
    h=h_
    title=title_

def create():
    global vmem, renderer, texture, window, w, h, title
    # Crear memoria de video (RGB)
    vmem = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Crear ventana
    sdl2.ext.init()
    window = sdl2.ext.Window(title, size=(w, h))
    window.show()

    # Crear renderizador
    renderer = sdl2.ext.Renderer(window)

    # Crear textura
    texture = sdl2.SDL_CreateTexture(renderer.renderer,
                                    sdl2.SDL_PIXELFORMAT_RGB24,
                                    sdl2.SDL_TEXTUREACCESS_STREAMING,
                                    w, h)

def event():
    for event in sdl2.ext.get_events():
        if event.type == sdl2.SDL_QUIT:
            return (-1, "EXIT WINDOWS")
    return (0, None)

def render(call):
    global vmem

    for i in call:
        op, argv = i[0], i[1]
        match op:
            case 0:
                # por ejemplo, dibujar pixel
                x, y, color = argv
                vmem[y, x] = color
            case 1:
                # dibujar rectángulo
                x, y, w_, h_, color = argv
                vmem[y:y+h_, x:x+w_] = color

    # Dbujar la memoria
    sdl2.SDL_UpdateTexture(texture, None, vmem.ctypes.data, w*3)
    sdl2.SDL_RenderCopy(renderer.renderer, texture, None, None)
    vmem.fill(0)

    # Presentar cambios
    renderer.present()

def exit():
    global initinstance
    sdl2.ext.quit()
    initinstance = False

if __name__ == "__main__":
    start(600, 600, "Mi ventana SDL2")
    create()

    running = True
    while running:
        code, msg = event() or (0, None)
        if code == -1:
            break

        # Comandos para renderizar
        calls = [
            [0, [10, 10, [255, 0, 0]]],           # Pixel rojo
            [1, [20, 20, 15, 15, [0, 255, 0]]],   # Rectángulo verde
        ]
        render(calls)

    exit()