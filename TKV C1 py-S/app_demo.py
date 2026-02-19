# app_demo.py - demo app: creates a window and draws a movable circle inside it

def init(calls):
    # create window, store its id in a global var so system can find it
    win_id = calls(["window", "create", 120, 80, 260, 180, "Demo"])
    # store win position/size in globals so system can read/move them
    calls(["var_global", f"win_pos_{win_id}"])[0] = (120,80)
    calls(["var_global", f"win_size_{win_id}"])[0] = (260,180)

    # app local state
    calls(["var_local", "x"])[0] = 200
    calls(["var_local", "y"])[0] = 170
    calls(["var_local", "r"])[0] = 20
    calls(["var_local", "win_id"])[0] = win_id

def code(calls):
    mx,my,ml,mr = calls(["get","mouse"])
    k = calls(["get","key"])

    win_id = calls(["var_local","win_id"])[0]
    wx,wy = calls(["var_global", f"win_pos_{win_id}"])[0]
    ww,wh = calls(["var_global", f"win_size_{win_id}"])[0]

    x = calls(["var_local","x"])[0]
    y = calls(["var_local","y"])[0]
    r = calls(["var_local","r"])[0]

    # move with WASD
    if k == 119: y -= 3
    if k == 115: y += 3
    if k == 97:  x -= 3
    if k == 100: x += 3

    # if left click inside window, teleport circle to mouse (coords are global)
    if ml and (wx <= mx <= wx+ww and wy <= my <= wy+wh):
        x = mx
        y = my

    # clamp inside window
    x = max(wx+ r, min(wx+ww - r, x))
    y = max(wy+ r+24, min(wy+wh - r, y))  # +24 avoid titlebar

    calls(["var_local","x"])[0] = x
    calls(["var_local","y"])[0] = y

    # draw window frame (simple) and content: titlebar + circle
    # window rect background
    calls(["draw","rect", wx, wy, ww, wh, (200,200,200)])
    # title bar
    calls(["draw","rect", wx, wy, ww, 24, (60,90,160)])
    calls(["draw","text", wx+6, wy+4, f"Demo - id {win_id}", (255,255,255)])
    # circle content
    calls(["draw","circle", int(x), int(y), int(r), (180,30,30)])
