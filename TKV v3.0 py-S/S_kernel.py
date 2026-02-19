# 1. Pipes / IPC                           | Transferencia de memoria entre procesos, flush / read / write                     | 10%
# 2. Scheduler avanzado                    | Round-robin, prioridades, sleep / wake-up                                         | 20%
# 3. Estados extendidos F_exec             | 02 01 (interrupción teclado), 10 FF / 11 00 (sleep dec/inc), ff ff (overflow CPU) | 15%
# 4. Interrupciones internas y drivers     | Timers, señales virtuales, drivers dinámicos                                      | 10%
# 5. I/O real                              | Teclado, mouse, GPU completo, puertos configurables                               | 15%
# 6. Memoria compartida / ABI              | termock-header, pipes en memoria                                                  | 5%
# 7. Gestión de errores y flags extendidos | HALT, MMU, overflow, flags adicionales                                            | 30%
# 8. Soporte de formatos ejecutables       | OA completo, ELF y MZ planeados                                                   | 50%
# 9. Debug y logging                       | Consola clara, logs de procesos                                                   | 20%

# S_kernel - kernel

import sys
import pathlib
import copy

# compatibilidad
import S_kernel_port.S_exec_open.F_STD_OA as F_OA

G_MEM = None
G_MMU = []
H_cpu = None
initk = ""

def init(H_CPU, MEM, initk_):
    global H_cpu, G_MEM, initk
    H_cpu = H_CPU
    G_MEM = MEM
    initk = initk_
    print("[ OK ] initk", initk)

G_context_suk = [
    0,  # F_exec
    0,  # F_type
    0,  # RING
    [[0,0,2**10,0b111]], # mmu
    0,  # PID
    0,  # FPID
    bytearray(18*2)  # registros
]

internal_service = {
    0: [
        0xE7, 0x00,       # OUT 0x01 (envía algo al puerto 1, ejemplo)
        0xB8, 0x34, 0x12, # MOV AX, 0x1234 (opcional, prepara datos)
        0xE7, 0x00,       # OUT AX, 0x01 (puedes usar AX si quieres enviar valor)
        0xCF              # IRET - devolver al kernel
    ]
}

# debug
DEBUG = False

F_formats = [
    F_OA
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
    global G_MMU, G_MEM, G_pid, G_num_procs
    mainoffset=G_context[3][1][0]
    if regs[0]==0x0300:
        root=""
        while True:
            char=G_MEM[regs[5]+mainoffset]
            regs[5]+=1
            if char==0xff: break
            root+=chr(char)
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
        print(f"[ OK ] LOADING /{root}")
    elif regs[0]==0x3303:
        suk = copy.deepcopy(G_context_suk)
        H_cpu.cpu(None, suk, internal_service[0], steps=-1)
    elif regs[0]==0xFFFF:
        if G_context[2]==0:
            print("[ OK ] shut down")
            sys.exit()

    return regs

# --- EXECUTE MODULES ----------------------------------------------------
PCB_size = 64  # total PCB
HEADER_SIZE = 8  # header = 8 bytes

def scheduler():
    global G_context, G_MEM, G_MMU, G_pid, G_num_procs, H_cpu

    for i in range(G_num_procs):
        regs_offset = i * PCB_size

        # --- HEADER del contexto ---
        F_exec = (G_MEM[regs_offset + 0] & 0xFF) | (G_MEM[regs_offset + 1] << 8)
        F_type = G_MEM[regs_offset + 2]  # MOD_ID
        ring   = G_MEM[regs_offset + 3]
        pid    = (G_MEM[regs_offset + 4] & 0xFF) | (G_MEM[regs_offset + 5] << 8)
        fpid   = (G_MEM[regs_offset + 6] & 0xFF) | (G_MEM[regs_offset + 7] << 8)

        # --- REGISTROS / ARGUMENTOS ---
        regs = G_MEM[regs_offset + HEADER_SIZE : regs_offset + PCB_size]  # 56 bytes para registros

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
        G_context = [
            F_exec,
            F_type,
            ring,            # RING
            G_MMU[pid],      # segmento/código
            pid,             # PID
            fpid,            # FPID
            regs,            # registros
        ]
        if F_exec==0x0101:
            ex = H_cpu.cpu(calls, G_context, G_MEM)
        else:
            ex = -1
            sys.exit()

        if ex == -1:
            if ring==0:
                print(f"STOP CODE [HALT] FOR RING {ring} (PID {pid}) Denegate")
            else:
                regs[0] = 0x01     # F_exec low byte
                regs[1] = 0x01     # F_exec high byte
        elif ex == -2:
            print(f"STOP CODE [MMU] FOR RING {ring} (PID {pid}) Denegate")
            
        # Guardar los registros actualizados de vuelta en G_MEM
        G_MEM[regs_offset + HEADER_SIZE : regs_offset + PCB_size] = regs

G_loop        = True
G_context     = None
G_pid         = 0
G_num_procs   = 0

ROOT_DIR = pathlib.Path(__file__).parent.resolve()

def loadinitk():
    global G_MMU, G_MEM, G_pid, G_num_procs
    with open(ROOT_DIR / "C" / initk, "rb") as file: # system loader
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
    print("[ OK ] LOAD initk")

# --- MAIN LOOP ----------------------------------------------------------
def S_kernel():
    while G_loop:
        scheduler()
        if DEBUG:
            clear_console()
