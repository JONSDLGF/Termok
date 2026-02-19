# app_clock.py - shows current time in a window

import time

def init(calls):
    win_id = calls(["window", "create", 420, 80, 240, 120, "Clock"])
    calls(["var_global", f"win_pos_{win_id}"])[0] = (420,80)
    calls(["var_global", f"win_size_{win_id}"])[0] = (240,120)
    calls(["var_local","win_id"])[0] = win_id

def code(calls):
    win_id = calls(["var_local","win_id"])[0]
    wx,wy = calls(["var_global", f"win_pos_{win_id}"])[0]
    ww,wh = calls(["var_global", f"win_size_{win_id}"])[0]
    t = time.strftime("%H:%M:%S")

    # draw window
    calls(["draw","rect", wx, wy, ww, wh, (220,220,220)])
    calls(["draw","rect", wx, wy, ww, 24, (100,100,180)])
    calls(["draw","text", wx+8, wy+6, f"Clock", (255,255,255)])
    calls(["draw","text", wx+20, wy+40, t, (10,10,10)])
