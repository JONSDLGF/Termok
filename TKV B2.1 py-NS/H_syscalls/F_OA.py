# F_OA.py - Módulo OA

magic_code = b"OA"
MOD_ID     = 0

# Tamaños de registros y offsets
SIZE_REGS_BLOCK = 27  # 9 regs de 2B + FLAGS 1B + PID 2B + FPID 2B + RING 1B
OFFSET_SEGMENTS = SIZE_REGS_BLOCK  # empezamos después de regs
HEADER_SIZE = 256  # bytes a saltar

def getcode(BIN: bytearray) -> tuple[int, int, list[tuple[int,int]]]:
    """
    Extrae los punteros de segmentos del binario OA.
    Retorna:
    0, MOD_ID, lista de tuplas (inicio, fin) de cada segmento
    """
    if BIN[:len(magic_code)] != magic_code:
        return -1

    # Header OA: db "OA", db 0, dw size_table_sectors
    header_start  = 3
    table_sectors_start = BIN[header_start]   | (BIN[header_start+1] << 8)
    table_sectors_size  = BIN[header_start+2] | (BIN[header_start+3] << 8)

    sectors = []
    # Cada 2 bytes es un puntero de segmento en little endian
    for i in range(table_sectors_start, table_sectors_start + table_sectors_size, 4):
        start = BIN[i] | (BIN[i+1] << 8)
        end   = BIN[i+2] | (BIN[i+3] << 8)
        sectors.append((start, end))

    return 0, MOD_ID, sectors

def load(G_MEM: bytearray, G_MMU: list, PID: int, sectors, BIN: bytearray, FPID, RING, modid):

    # ----------------------------------------
    # Inicializar bloque de registros
    # ----------------------------------------
    regs_offset = PID * SIZE_REGS_BLOCK
    for i in range(SIZE_REGS_BLOCK):
        G_MEM[regs_offset + i] = 0

    # PID
    G_MEM[regs_offset + 19] = PID & 0xFF
    G_MEM[regs_offset + 20] = (PID >> 8) & 0xFF

    # FPID
    G_MEM[regs_offset + 21] = FPID & 0xFF
    G_MEM[regs_offset + 22] = (FPID >> 8) & 0xFF

    # RING
    G_MEM[regs_offset + 23] = RING
    G_MEM[regs_offset + 24] = modid

    # F_exec = 0x0101
    G_MEM[regs_offset + 25] = 0x01
    G_MEM[regs_offset + 26] = 0x01

    # ----------------------------------------
    # Cargar segmentos SIN HEADER
    # ----------------------------------------
    current_addr = len(G_MEM)

    if PID >= len(G_MMU):
        G_MMU.append([])

    for index, (orig_l_start, orig_l_end) in enumerate(sectors):

        # Quitar header → convertir a local relativo
        l_start = orig_l_start - HEADER_SIZE
        l_end   = orig_l_end   - HEADER_SIZE

        size = l_end - l_start

        if size <= 0:
            print("[ERR] Segmento vacío o inválido")
            continue

        # Copiar datos reales sin header
        G_MEM.extend(BIN[orig_l_start:orig_l_end])

        # Permisos
        perms = 0b001 if index == 0 else 0b110  # primer sector ejecutable

        # Añadir a la MMU con local corregido
        G_MMU[PID].append([current_addr, l_start, l_end, perms])

        # Avanzar dirección global
        current_addr += size

    return G_MEM, G_MMU
