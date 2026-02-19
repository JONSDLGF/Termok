# system.py - gestor de ventanas / escritorio / launcher
# usa la API 'calls' del kernel

# simple desktop manager that can exec apps by name and draw windows + a taskbar

APPS = [("Demo", "app_demo"), ("Clock", "app_clock")]

def init(calls):
    # desktop variables
    calls(["var_local", "wins"])  # will hold list of window ids created by this sys
    calls(["var_local", "mouse_down"])  # helper
    calls(["var_local", "drag_win"])    # index of dragging window or -1
    calls(["var_local", "drag_off_x"])
    calls(["var_local", "drag_off_y"])
    # create a taskbar
    calls(["var_local", "taskbar_h"])
    calls(["var_local", "taskbar_h"])[0] = 32
    calls(["var_local", "wins"])[0] = []

    # draw desktop wallpaper and launcher buttons every frame in code()

def code(calls):
    # read mouse
    mx,my,ml,mr = calls(["get","mouse"])
    # locals
    wins_ref = calls(["var_local", "wins"])
    wins = wins_ref[0]
    drag_ref = calls(["var_local", "drag_win"])
    if drag_ref[0] is None:
        drag_ref[0] = -1
    mouse_down_ref = calls(["var_local", "mouse_down"])
    if mouse_down_ref[0] is None:
        mouse_down_ref[0] = False

    # draw desktop background
    calls(["draw", "rect", 0,0,800,480, (30,30,50)])
    # draw taskbar
    tb_h = calls(["var_local", "taskbar_h"])[0] or 32
    calls(["draw", "rect", 0,480-tb_h,800,tb_h, (40,40,60)])

    # draw launcher buttons on taskbar
    x = 6
    for name, modname in APPS:
        calls(["draw","rect", x, 480-tb_h+4, 80, tb_h-8, (70,70,100)])
        calls(["draw","text", x+6, 480-tb_h+10, name, (220,220,220)])
        # click detection (simple)
        if ml and (x <= mx <= x+80) and (480-tb_h+4 <= my <= 480-tb_h+4+tb_h-8):
            # exec app
            calls(["exec", modname])
        x += 88

    # draw existing windows (system doesn't own their contents; apps draw into screen via calls)
    # we just draw window frames stored in kernel _windows; since kernel stores windows we can't access directly,
    # instead each app creates its own window and draws. We'll draw simple frames here by probing our local wins list.
    # For simplicity, system expects apps to create windows and draw themselves.

    # handle dragging: detect click on any app's titlebar (we will ask apps to set a var "titlebar" when created)
    # Very simple: on mouse left press, check all windows created by this system (we tracked ids in wins list)
    if ml and not mouse_down_ref[0]:
        # press happened now
        mouse_down_ref[0] = True
        # check windows top-to-bottom: wins list is order created: assume last is top
        for wid in reversed(wins):
            # read app-local var "title" and "rect" (convention: apps set these local vars)
            # we can't read other module's locals directly except via var_local for the running G_call (system).
            # Instead, use kernel global convention: apps MUST set global var "win_pos_{id}" and "win_size_{id}"
            pos = calls(["var_global", f"win_pos_{wid}"])[0]
            size = calls(["var_global", f"win_size_{wid}"])[0]
            if pos is None or size is None:
                continue
            wx,wy = pos
            ww,wh = size
            # titlebar area: wx,wy .. wx+ww, wy+24
            if wx <= mx <= wx+ww and wy <= my <= wy+24:
                # begin dragging
                drag_ref[0] = wid
                calls(["var_local", "drag_off_x"])[0] = mx - wx
                calls(["var_local", "drag_off_y"])[0] = my - wy
                break
    elif not ml:
        mouse_down_ref[0] = False
        # drop dragging
        if drag_ref[0] != -1:
            drag_ref[0] = -1

    # if dragging, move the window by setting its global pos
    if drag_ref[0] not in (None, -1):
        wid = drag_ref[0]
        offx = calls(["var_local", "drag_off_x"])[0] or 0
        offy = calls(["var_local", "drag_off_y"])[0] or 0
        calls(["var_global", f"win_pos_{wid}"])[0] = (mx - offx, my - offy)

    # finally, draw a cursor square
    calls(["draw", "rect", mx-6, my-6, 12, 12, (255,255,255)])
