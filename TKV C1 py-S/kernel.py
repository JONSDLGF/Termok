# main.py - kernel / engine
import pygame as pg
import sys
import pathlib
import importlib

# Paths
ROOT_DIR = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(ROOT_DIR))

# Core modules: arrancamos el gestor 'system' por defecto
import system

_eng_implement = [[False, system]]   # cada item: [started(bool), module]
_eng_vars_local = {}                 # var locales por módulo (dict of dict)
_eng_vars_global = {}                # var globales (dict name -> [value])
_windows = []                        # windows: list of dicts

# Input / state globals
G_key: int = 0
G_key_pressed: bool = False

G_mouse_x: int = 0
G_mouse_y: int = 0
G_mouse_click_L: bool = False
G_mouse_click_R: bool = False

G_loop: bool = True
G_call = None

# Config
SIZE = (800, 480)
DEBUG = False

# Pygame init
pg.init()
screen = pg.display.set_mode(SIZE)
clock = pg.time.Clock()
font = pg.font.SysFont("Consolas", 14)

# Aux
def clear_console():
    sys.stdout.write("\x1b[3J\x1b[2J\x1b[H")
    sys.stdout.flush()

# --- ENGINE API (syscalls) ----------------------------------------------
def calls(argv: list):
    """
    Universal kernel syscall:
      - var_local / var_global  => returns a reference list [value] (mutable)
      - exec module_name        => dynamically import & schedule module
      - get key/mouse/mouse_button/key_down
      - draw primitives: rect, pix, line, circle, text
      - window: create / draw (simple)
      - log
    """
    global G_call, _eng_implement, _eng_vars_global, _windows

    if G_call is None:
        return None

    module_name = G_call.__name__
    # ensure local space exists
    if module_name not in _eng_vars_local:
        _eng_vars_local[module_name] = {}

    op = argv[0]

    # VAR LOCAL (returns mutable container)
    if op == "var_local":
        name = argv[1]
        d = _eng_vars_local[module_name]
        d.setdefault(name, [None])
        return d[name]

    # VAR GLOBAL
    if op == "var_global":
        name = argv[1]
        _eng_vars_global.setdefault(name, [None])
        return _eng_vars_global[name]

    # EXEC: import module by name and add to schedule (if not present)
    if op == "exec":
        name = argv[1]
        # if already loaded, bring to front / mark as started
        for mod_entry in _eng_implement:
            if mod_entry[1].__name__ == name:
                # nothing special: ensure started and call init next loop if needed
                return True
        # try dynamic import
        try:
            mod = importlib.import_module(name)
            _eng_implement.append([False, mod])
            return True
        except Exception as e:
            print(f"[kernel exec] error importing {name}: {e}")
            return False

    # GETs
    if op == "get":
        t = argv[1]
        if t == "key":
            return G_key if G_key_pressed else None
        if t == "key_down":
            # argv[2] is pg key constant or integer
            keys = pg.key.get_pressed()
            return keys[argv[2]]
        if t == "mouse":
            return (G_mouse_x, G_mouse_y, G_mouse_click_L, G_mouse_click_R)
        if t == "mouse_button":
            b = argv[2]
            if b == "L": return G_mouse_click_L
            if b == "R": return G_mouse_click_R
            return False

    # LOG
    if op == "log":
        print("[LOG]", argv[1])
        return None

    # DRAW primitives
    if op == "draw":
        t = argv[1]
        if t == "rect":
            x,y,w,h,color = argv[2],argv[3],argv[4],argv[5],argv[6]
            pg.draw.rect(screen, color, (x,y,w,h))
        elif t == "pix":
            x,y,color = argv[2],argv[3],argv[4]
            if 0 <= x < SIZE[0] and 0 <= y < SIZE[1]:
                screen.set_at((int(x),int(y)), color)
        elif t == "line":
            x1,y1,x2,y2,color = argv[2],argv[3],argv[4],argv[5],argv[6]
            pg.draw.line(screen, color, (x1,y1), (x2,y2))
        elif t == "circle":
            x,y,r,color = argv[2],argv[3],argv[4],argv[5]
            pg.draw.circle(screen, color, (int(x),int(y)), int(r))
        elif t == "text":
            x,y,text,color = argv[2],argv[3],argv[4],argv[5]
            surf = font.render(str(text), True, color)
            screen.blit(surf, (x,y))
        return None

    # Simple window manager primitives
    if op == "window":
        t = argv[1]
        if t == "create":
            x,y,w,h,title = argv[2],argv[3],argv[4],argv[5],argv[6]
            win = {"x":x,"y":y,"w":w,"h":h,"title":title,"z":len(_windows)}
            _windows.append(win)
            return len(_windows)-1
        if t == "draw":
            # ["window","draw", win_id, "rect", x,y,w,h,color]  (coords relative to window)
            win_id = argv[2]
            action = argv[3]
            if 0 <= win_id < len(_windows):
                win = _windows[win_id]
                wx,wy = win["x"], win["y"]
                if action == "rect":
                    _,_,rx,ry,rw,rh,color = argv
                    pg.draw.rect(screen, color, (wx+rx, wy+ry, rw, rh))
                elif action == "text":
                    _,_,_,tx,ty,text,color = argv
                    surf = font.render(str(text), True, color)
                    screen.blit(surf, (wx+tx, wy+ty))
            return None

    return None

# --- INPUT --------------------------------------------------------------
def stdin():
    global G_key, G_key_pressed
    global G_mouse_x, G_mouse_y, G_mouse_click_L, G_mouse_click_R
    global G_loop

    G_key_pressed = False
    # mouse buttons keep state on MOUSEBUTTONUP / DOWN
    for event in pg.event.get():
        if event.type == pg.QUIT:
            G_loop = False
        elif event.type == pg.KEYDOWN:
            G_key = event.key
            G_key_pressed = True
        elif event.type == pg.MOUSEMOTION:
            G_mouse_x, G_mouse_y = event.pos
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1: G_mouse_click_L = True
            if event.button == 3: G_mouse_click_R = True
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1: G_mouse_click_L = False
            if event.button == 3: G_mouse_click_R = False

# --- EXECUTE MODULES ---------------------------------------------------
def code():
    global G_call
    # iterate copy: modules may append themselves
    for module_data in list(_eng_implement):
        started, module = module_data
        G_call = module
        try:
            if not started:
                module.init(calls)
                module_data[0] = True
            else:
                module.code(calls)
        except Exception as e:
            print(f"[kernel] error in module {module.__name__}: {e}")

# --- RENDER -------------------------------------------------------------
def render():
    pg.display.flip()
    screen.fill((20,20,30))  # desktop bg

# --- MAIN LOOP ----------------------------------------------------------
while G_loop:
    stdin()
    code()
    render()
    if DEBUG:
        clear_console()
        print("KEY:", G_key)
        print("GLOBAL:", _eng_vars_global)
        print("LOCAL:", _eng_vars_local)
        print("WINS:", _windows)
    clock.tick(60)
