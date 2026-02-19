# H_kernel.py - kernel

# nota:
# code() mas preciso en el tipo de proceso                           [0%]
# syscall que sea lo esencial como llamar a drivers o a subdrivers   [50%]
# crear un G_VMEM                                                    [0%]
# crear un driver de video                                           [0%]
# G_MMU, G_MEM solo memoria asignada y paginacion                    [OK]

import pygame as pg
import sys
import pathlib

# cpu x86
import H_cpu
import H_syscalls.F_LINUX as F_LINUX
import H_syscalls.F_OA    as F_OA
import H_syscalls.F_ELSE  as F_ELSE

# Config screen
SIZE  = (640, 480)
G_VMEM = bytearray(SIZE[0]*SIZE[1]*3)

G_MEM = bytearray(2**10)
G_MMU = []

# debug
DEBUG = False

F_formats = [
    F_OA,
    F_LINUX,
    F_ELSE
]

# funcs
def desheader(BIN):
    """
    desheader es el que extrae y verifica la integridad del archibo
    puede ser un ejecutable o otros, para los ejecutables se le da
    un id unico a cada sistema ejem:
        0 -> OA file
        1 -> ELF
        2 -> MZ
    return  1              -> archibo de aplicacion
    return  0, id, sectors -> archibo ejecutable
    return -1              -> error
    """
    global _procs
    for i in F_formats:
        if BIN[:len(i.magic_code)]==i.magic_code:
            return i.getcode(BIN)
    else: return -1

# Aux
def clear_console():
    sys.stdout.write("\x1b[3J\x1b[2J\x1b[H")
    sys.stdout.flush()

# --- ENGINE API (syscalls) ----------------------------------------------

def calls(regs):
    """
    Ejecuta un syscall para el kernel simulado.

    ```
    Parámetros:
    -----------
    ring : int
        Nivel de privilegio o contexto del proceso (no usado activamente aquí).
    regs : list[int]
        Lista de registros que representa los registros del proceso:
        [AX, BX, CX, DX, SI, DI]

        - AX: Código del syscall. Los 8 bits altos identifican la categoría
              y los 8 bits bajos identifican la operación dentro de la categoría.
        - BX, CX, DX: Parámetros de entrada/salida, dependiendo del syscall.
        - SI, DI: Uso general o desplazamiento en memoria.

    Retorno:
    --------
    list[int]
        Lista de registros actualizada después de ejecutar el syscall.

    Syscalls soportados:
    --------------------
    0x00 -> exit
        - Termina el proceso actual.
        - Parámetros: ninguno

    0x01 -> commands device
        - Ejecuta comandos de dispositivo (no implementado aún).

    0x03 -> exec
        - Carga y ejecuta un archivo en memoria.
        - Parámetros:
            SI: puntero al nombre del archivo en memoria
        - Modifica:
            G_MEM, G_MMU, G_pid

    0x0E -> stdout write a text
        - Escribe texto en la salida estándar.
        - Parámetros:
            SI: puntero al buffer de texto en memoria
        - Modifica: ningún registro, imprime en pantalla

    0x0F -> graphics
        - Sub-syscalls gráficos:
            0x00 -> placeholder (sin acción)
            0x01 -> monocrome pixel
                - In:  BX -> x, CX -> y, DX -> color
                - Out: BX, CX, DX (sin cambios)
                - Dibuja un píxel monocromo en pantalla.
            0x02 -> rect color24
                - In:  BX -> offset del rect en memoria
                    Contenido de memoria: [w_lo, w_hi, h_lo, h_hi, x_lo, x_hi, y_lo, y_hi, r, g, b]
                - Dibuja un rectángulo de color 24 bits.
            0x03 -> color24 image
                - In:  BX -> offset image, CX -> offset x, DX -> offset y
                    Contenido de memoria: [w_lo, w_hi, h_lo, h_hi, data]
                - Out: ninguno
                - Dibuja imagen 24 bits desde memoria
            0x04 -> color32 image
                - In:  BX -> offset image, CX -> offset x, DX -> offset y
                    Contenido de memoria: [w_lo, w_hi, h_lo, h_hi, data]
                - Out: ninguno
                - Dibuja imagen 32 bits desde memoria

    0x10 -> keyboard
        - Sub-syscall:
            0x00 -> getkey and key state
                - Out: BX -> tecla, CX -> estado (1=presionada, 0=libre)

    0x33 -> mouse
        - Sub-syscalls:
            0x00 -> toggle mouse (activa/desactiva y visibilidad)
            0x03 -> mouse state
                - Out: BX -> botones (bit0=L, bit1=R)
                    CX -> x, DX -> y (posición del mouse)
    """
    global DEBUG, G_MEM, G_MMU, G_pid, G_mouse, G_call_module, G_num_procs

    mainoffset = G_call_module[4][0][0]
    call       = regs[0]>>8
    callcode   = regs[0]&0xFF

    if DEBUG:
        print(f"[CALL] {call:2X} {callcode:2X}")

    if call == 0x00:
        G_call_module[6] = 0x00 << 8 | callcode
        return 0

    elif call == 0x01:
        pass  # commands of device

    elif call == 0x03:
        root=""
        while True:
            char=G_MEM[regs[5]+mainoffset]
            if char==0xff: break
            root+=chr(char)
            regs[5]+=1
        try:
            with open(ROOT_DIR / "C" / root, "rb") as file:
                mainbin = file.read()
        except Exception as err:
            print(f"file not find: {err}")
            return regs

        F = desheader(mainbin)
        if F == -1:
            print("[err] header")
            sys.exit(-1)

        for fmt in F_formats:
            if fmt.MOD_ID == F[1]:
                G_MEM, G_MMU = fmt.load(G_MEM, G_MMU, G_pid, F[2], mainbin, 0, 0, F[1])
        
        G_pid += 1
        G_num_procs += 1

    elif call==0x0E:
        while True:
            char=G_MEM[regs[5]+mainoffset]
            if char==0xff: break
            sys.stdout.write(chr(int(char)))
            regs[5]+=1
        sys.stdout.flush()

    elif call==0x0F:
        if callcode == 0x00:
            pass
        elif callcode == 0x01:
            screen.set_at((regs[1],regs[2]), tuple([regs[3]]*3))

        elif callcode == 0x02:
            w = (G_MEM[regs[1]+mainoffset+1]<<8) | G_MEM[regs[1]+mainoffset]
            h = (G_MEM[regs[1]+mainoffset+3]<<8) | G_MEM[regs[1]+mainoffset+2]
            x = (G_MEM[regs[1]+mainoffset+5]<<8) | G_MEM[regs[1]+mainoffset+4]
            y = (G_MEM[regs[1]+mainoffset+7]<<8) | G_MEM[regs[1]+mainoffset+6]
            r = G_MEM[regs[1]+mainoffset+8]
            g = G_MEM[regs[1]+mainoffset+9]
            b = G_MEM[regs[1]+mainoffset+10]
            pg.draw.rect(screen, (r,g,b), pg.Rect(x, y, w, h))

        elif callcode == 0x03:
            w = (G_MEM[regs[1]+mainoffset+1]<<8) | G_MEM[regs[1]+mainoffset]
            h = (G_MEM[regs[1]+mainoffset+3]<<8) | G_MEM[regs[1]+mainoffset+1]
            offsetx = regs[2]
            offsety = regs[3]
            for i in range(w):
                for j in range(h):
                    screen.set_at(
                        (
                            i+offsetx,
                            j+offsety
                        ),(
                            G_MEM[regs[1] + mainoffset + 3*(i + j*regs[1]&0xFF)],
                            G_MEM[regs[1] + mainoffset + 3*(i + j*regs[1]&0xFF)+1],
                            G_MEM[regs[1] + mainoffset + 3*(i + j*regs[1]&0xFF)+2],
                        )
                    )
        elif callcode == 0x04:
            w = (G_MEM[regs[1]+mainoffset+1]<<8) | G_MEM[regs[1]+mainoffset]
            h = (G_MEM[regs[1]+mainoffset+3]<<8) | G_MEM[regs[1]+mainoffset+2]
            offsetx = regs[2]
            offsety = regs[3]
            imgoffset = regs[1] + mainoffset + 4
            for i in range(w):
                for j in range(h):
                    if G_MEM[imgoffset + 4*(i + j*w)+3]==0xFF:
                        screen.set_at(
                            (
                                i+offsetx,
                                j+offsety
                            ),(
                                G_MEM[imgoffset + 4*(i + j*w)],
                                G_MEM[imgoffset + 4*(i + j*w)+1],
                                G_MEM[imgoffset + 4*(i + j*w)+2],
                            )
                        )

    elif call == 0x10:
        if callcode == 0x00:
            regs[1] = G_key
            regs[2] = int(G_key_pressed)

    elif call == 0x33:
        if callcode == 0:
            G_mouse = not G_mouse
            pg.mouse.set_visible(not G_mouse)
        elif callcode == 3 and G_mouse:
            regs[1] = (G_mouse_click_R << 1) | G_mouse_click_L
            regs[2] = G_mouse_x
            regs[3] = G_mouse_y

    return regs


# --- INPUT --------------------------------------------------------------
def stdin():
    global G_key, G_key_pressed
    global G_mouse_x, G_mouse_y, G_mouse_click_L, G_mouse_click_R, G_mouse
    global G_loop

    # mouse buttons keep state on MOUSEBUTTONUP / DOWN
    for event in pg.event.get():
        if event.type == pg.QUIT:
            G_loop = False
        elif event.type == pg.KEYDOWN:
            G_key = event.key
            G_key_pressed = True
        elif event.type == pg.KEYUP:
            G_key_pressed = False
        elif event.type == pg.MOUSEMOTION:
            G_mouse_x, G_mouse_y = event.pos
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1: G_mouse_click_L = True
            if event.button == 3: G_mouse_click_R = True
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1: G_mouse_click_L = False
            if event.button == 3: G_mouse_click_R = False

# --- EXECUTE MODULES ----------------------------------------------------
def code():
    global G_call_module, G_MEM, G_MMU, G_pid, G_num_procs
    SIZE_REGS_BLOCK = 27

    # 
    for i in range(G_num_procs):
        regs_offset = i*SIZE_REGS_BLOCK
        regs = G_MEM[regs_offset:regs_offset+SIZE_REGS_BLOCK]

        pid    = (regs[19] & 0xFF) | (regs[20] << 8)
        fpid   = (regs[21] & 0xFF) | (regs[22] << 8)
        ring   = regs[23]
        F_type = regs[24]
        F_exec = (regs[25] & 0xFF) | (regs[26] << 8)

        # F_exec
        #  00 00 -> none
        #  00 01 -> run
        #  00 02 -> whait
        #  01 XX -> exit(0xXX)
        #  02 00 -> interump exit
        #  02 01 -> interump key code
        #  10 FF -> sleep 255 and dec
        #  11 00 -> sleep   0 and inc
        #  ff ff -> cpu overflow detected (pc fuera de rango)

        # Preparar contexto para la CPU simulada
        G_call_module = [
            regs,            # registros
            pid,             # PID
            fpid,            # FPID
            ring,            # RING
            G_MMU[pid],      # segmento/código
            F_type,
            F_exec
        ]

        if F_exec==0x0001:
            # Ejecutar CPU simulada steps = 255
            ex = H_cpu.cpu(ring, regs, G_MEM, G_MMU[pid], calls)
        else:
            ex = -2

        if ex == -1:
            if ring==0:
                print(f"STOP CODE [HALT] FOR RING {ring} (PID {pid}) Denegate")
            else:
                regs[25] = 0x01     # F_exec low byte
                regs[26] = 0x01     # F_exec high byte
        elif ex == -2:
            print(f"STOP CODE [MMU] FOR RING {ring} (PID {pid}) Denegate")
            sys.exit()

        # Guardar los registros actualizados de vuelta en G_MEM
        G_MEM[regs_offset : regs_offset + SIZE_REGS_BLOCK] = regs


# --- RENDER -------------------------------------------------------------
def render():
    clock.tick(60)
    pg.display.flip()
    screen.fill((20,20,20))


# --- main code ----------------------------------------------------------

G_key: int = 0
G_key_pressed: bool = False

G_mouse: bool = False
G_mouse_x: int = 0
G_mouse_y: int = 0
G_mouse_click_L: bool = False
G_mouse_click_R: bool = False

# secion de memoria de kernel solo el kernel puede apceder a ellos
# --- start syscalls -----------------------------------------------------

# call any for syscall extern:
#  call for an driver:
#   stop pid proc set flag device=1
#   ...
#   driver tasklist() -> if device=1
#    use de driver
#   else
#    next

G_loop: bool = True
G_call_module = None
G_pid = 0
G_num_procs = 0
# fin

ROOT_DIR = pathlib.Path(__file__).parent.resolve()

# GRUB main proc

with open(ROOT_DIR / "C" / "main.bin", "rb") as file: # system loader
    mainbin = file.read()

F = desheader(mainbin)
if F==-1:
    print("[err] header")
    sys.exit(-1)

for fmt in F_formats:
    if fmt.MOD_ID == F[1]:
        G_MEM, G_MMU = fmt.load(G_MEM, G_MMU, G_pid, F[2], mainbin, 0, 0, F[1])

G_pid += 1
G_num_procs += 1

# Pygame init -> "screen load VGA"
pg.init()
screen = pg.display.set_mode(SIZE)
clock = pg.time.Clock()
font = pg.font.SysFont("Consolas", 14)

# --- MAIN LOOP ----------------------------------------------------------
#try:
while G_loop:
    stdin()
    code()
    render()
    if DEBUG:
        clear_console()
        print("KEY:", G_key)
#except Exception as ERR:
#    print(f"exit code [in loop] -> {ERR}")
