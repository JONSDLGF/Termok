import sys

def MMU(sect, pc, access_type):
    """
    Traduce una dirección local a global y verifica permisos.
    Devuelve la dirección global si es válida; si no, devuelve -1.

    sect: lista de segmentos:
          [global_start, local_start, size, perms]

    perms: bits
        0b100 = read
        0b010 = write
        0b001 = execute
        
    access_type: bits requeridos
    """

    for seg in sect:
        g_start = seg[0]
        l_start = seg[1]
        size    = seg[2]
        perms   = seg[3]

        # Verificar si PC está en el rango LOCAL
        if l_start <= pc < l_start + size:
            # Verificar permisos
            if (perms & access_type) != access_type:
                return -1  # Permisos insuficientes
            
            # Convertir local → global
            offset = pc - l_start
            global_addr = g_start + offset
            return global_addr

    # No pertenece a ningún segmento
    return -1

def ABSP(sect, pc):
    for seg in sect:
        g_start = seg[0]
        l_start = seg[1]
        size    = seg[2]

        # Verificar si PC está en el rango LOCAL
        if l_start <= pc < l_start + size:
            
            # Convertir local → global
            offset = pc - l_start
            global_addr = g_start + offset
            return global_addr
    # No pertenece a ningún segmento
    return -1

def alu(oper, bits, a, b, cf, zf, sf, of):
    mask = (1 << bits) - 1
    sign = 1 << (bits - 1)

    # --- Helpers ---
    def set_flags(result, carry, overflow):
        cf = carry
        zf = 1 if (result & mask) == 0 else 0
        sf = 1 if (result & sign) != 0 else 0
        of = overflow
        return cf, zf, sf, of

    # ========================
    #       ADD
    # ========================
    if oper == 0b0000:
        result = (a + b) & mask
        carry = 1 if (a + b) > mask else 0
        overflow = 1 if (~(a ^ b) & (a ^ result) & sign) else 0
        cf, zf, sf, of = set_flags(result, carry, overflow)
        return result, b, cf, zf, sf, of

    # ========================
    #       OR
    # ========================
    if oper == 0b0001:
        result = a | b
        cf, zf, sf, of = set_flags(result, 0, 0)
        return result & mask, b, cf, zf, sf, of

    # ========================
    #       AND
    # ========================
    if oper == 0b0100:
        result = a & b
        cf, zf, sf, of = set_flags(result, 0, 0)
        return result & mask, b, cf, zf, sf, of

    # ========================
    #       SUB
    # ========================
    if oper == 0b0101:
        result = (a - b) & mask
        carry = 1 if a < b else 0
        overflow = 1 if ((a ^ b) & (a ^ result) & sign) else 0
        cf, zf, sf, of = set_flags(result, carry, overflow)
        return result, b, cf, zf, sf, of

    # ========================
    #       XOR
    # ========================
    if oper == 0b0110:
        result = a ^ b
        cf, zf, sf, of = set_flags(result, 0, 0)
        return result & mask, b, cf, zf, sf, of

    # ========================
    #       CMP
    # ========================
    if oper == 0b0111:
        result = (a - b) & mask
        carry = 1 if a < b else 0
        overflow = 1 if ((a ^ b) & (a ^ result) & sign) else 0
        cf, zf, sf, of = set_flags(result, carry, overflow)
        return a, b, cf, zf, sf, of

    # ========================
    #       INC
    # ========================
    if oper == 0b1000:
        result = (a + 1) & mask
        overflow = 1 if ((a & sign) == 0 and (result & sign) != 0) else 0
        # CF no cambia en x86
        cf = cf
        zf = 1 if result == 0 else 0
        sf = 1 if (result & sign) else 0
        of = overflow
        return result, b, cf, zf, sf, of

    # ========================
    #       DEC
    # ========================
    if oper == 0b1001:
        result = (a - 1) & mask
        overflow = 1 if ((a & sign) != 0 and (result & sign) == 0) else 0
        cf = cf
        zf = 1 if result == 0 else 0
        sf = 1 if (result & sign) else 0
        of = overflow
        return result, b, cf, zf, sf, of

    raise ValueError(f"Operación ALU desconocida: {oper}")

# --- CPU virtual completo NO ---
def cpu(ring, argv, mem, sect, calls, steps=16):
    pc = argv[0]<<8  | argv[1]
    ax = argv[2]<<8  | argv[3]
    cx = argv[4]<<8  | argv[5]
    dx = argv[6]<<8  | argv[7]
    bx = argv[8]<<8  | argv[9]
    sp = argv[10]<<8 | argv[11]
    bp = argv[12]<<8 | argv[13]
    si = argv[14]<<8 | argv[15]
    di = argv[16]<<8 | argv[17]

    # --- Regmap: regcode a variable ---
    regmap16 = {
        0b000: 'ax',
        0b001: 'cx',
        0b010: 'dx',
        0b011: 'bx',
        0b100: 'sp',
        0b101: 'bp',
        0b110: 'si',
        0b111: 'di'
    }

    # --- Leer registro por código ---
    def reglod(code):
        global ax, cx, dx, bx, sp, bp, si, di
        if isinstance(code, int):
            regname = regmap16[code]
        else:
            regname = code  # si pasas 'AX' directo
        return globals()[regname]

    # --- Escribir registro por código ---
    def regsab(code, value):
        global ax, cx, dx, bx, sp, bp, si, di
        if isinstance(code, int):
            regname = regmap16[code]
        else:
            regname = code
        globals()[regname] = value & 0xFFFF  # 16 bits

    def calcular_direccion(mod, rm, disp=0):
        """
        Calcula la dirección efectiva de memoria según mod/rm en modo 16 bits
        regs16 = [BX, CX, DX, SP, BP, SI, DI, ...] o un diccionario {'BX':..}
        disp = desplazamiento opcional (8 o 16 bits)
        """
        # Asumimos regs16: [AX,BX,CX,DX,SP,BP,SI,DI] o diccionario

        if mod == 0b11:
            raise ValueError("mod=11 significa registro, no memoria")

        # Mapear r/m a fórmula de EA
        if rm == 0b000: addr = reglod('BX') + reglod('SI')
        elif rm == 0b001: addr = reglod('BX') + reglod('DI')
        elif rm == 0b010: addr = reglod('BP') + reglod('SI')
        elif rm == 0b011: addr = reglod('BP') + reglod('DI')
        elif rm == 0b100: addr = reglod('SI')
        elif rm == 0b101: addr = reglod('DI')
        elif rm == 0b110:
            if mod == 0b00:
                addr = disp      # dirección absoluta disp16
            else:
                addr = reglod('BP') + disp
        elif rm == 0b111: addr = reglod('BX')
        else:
            raise ValueError("r/m inválido")

        return addr & 0xFFFF  # dirección de 16 bits

    flags = argv[18]

    cf = (flags>> 0)&1
    zf = (flags>> 6)&1
    sf = (flags>> 7)&1
    of = (flags>>11)&1

    i = 0
    while i < steps:
        # --- verificación de ejecución ---
        global_pc = MMU(sect, pc, 0b001)
        if global_pc == -1:
            calls(regs=[0, 0, 0, 0, 0, 0])
            return -2
        
        opc=[]

        for i in range(16):
            opc.append(mem[global_pc+i])

        match opc[0]>>4:
            case 0x0:
                pc+=1
                match opc[0]&0xF:
                    case 0xF:
                        if opc[1]==0x05:
                            e = calls([ax, bx, cx, dx, si, di])
                            if isinstance(e,int):
                                return -1
                            ax, bx, cx, dx, si, di = e
                            pc+=1
                    case _:
                        debug(opc,[pc, ax, cx, dx, bx, sp, bp, si, di, flags])
            case 0x8:
                pc+=1
                match opc[0]&0xF:
                    case 3:
                        modrm = opc[1]
                        pc+=1
                        mod = (modrm >> 6) & 0b11
                        reg_op = (modrm >> 3) & 0b111  # /0..7 → oper ALU
                        rm = modrm & 0b111             # registro o memoria destino
                        imm8 = opc[2]
                        pc+=1
                        imm16 = imm8
                        if imm8 >= 0x80:
                            imm16 -= 0x100
                        disp = 0  # por defecto

                        # --- Obtener desplazamiento según mod ---
                        if mod == 0b01:  # disp8
                            disp = mem[pc]
                            pc += 1
                            # sign-extend
                            if disp >= 0x80:
                                disp -= 0x100
                        elif mod == 0b10:  # disp16
                            disp = mem[pc] | (mem[pc+1] << 8)
                            pc += 2
                        elif mod == 0b00 and rm == 0b110:  # dirección absoluta
                            disp = mem[pc] | (mem[pc+1] << 8)
                            pc += 2

                        # --- Obtener destino ---
                        if mod == 0b11:       # registro directo
                            dest = reglod(rm)
                        else:                  # memoria
                            addr = calcular_direccion(mod, rm, disp)
                            global_addr = MMU(sect, addr, 0b110)  # read/write
                            if global_addr == -1:
                                raise Exception("Acceso a memoria inválido")
                            dest = mem[global_addr]

                        # ejecutar operación
                        result, _, cf, zf, sf, of = alu(reg_op, 16, dest, imm16, cf, zf, sf, of)

                        # guardar resultado si no es CMP
                        if reg_op != 0b111:
                            if mod == 0b11:
                                regsab(rm,result)
                            else:
                                mem[global_addr] = result & 0xFFFF

                    case _:
                        debug(opc,[pc, ax, cx, dx, bx, sp, bp, si, di, flags])
            case 0xA:
                pc+=1
                match opc[0]&0xF:
                    case 0:
                        os   = opc[2]
                        pc  += 1
                        os <<= 8
                        os  |= opc[1]
                        pc  += 1

                        global_pc = MMU(sect, os, 0b100)
                        if global_pc == -1:
                            return -2
                        
                        ax = (ax & 0xFF00) | mem[global_pc]
                    case _:
                        debug(opc,[pc, ax, cx, dx, bx, sp, bp, si, di, flags])
            case 0xB:
                pc+=1
                match opc[0]&0xF:
                    case 8: # MOV AX, imm16
                        ax   = opc[2]
                        pc  += 1
                        ax <<= 8
                        ax  |= opc[1]
                        pc  += 1
                    case 0xB: # MOV BX, imm16
                        bx   = opc[2]
                        pc  += 1
                        bx <<= 8
                        bx  |= opc[1]
                        pc  += 1
                    case 0xF: # MOV DI, imm16
                        di   = opc[2]
                        pc  += 1
                        di <<= 8
                        di  |= opc[1]
                        pc  += 1
                    case _:
                        debug(opc,[pc, ax, cx, dx, bx, sp, bp, si, di, flags])
            case 0xE:
                pc+=1
                match opc[0]&0xF:
                    case 0xB:
                        os = opc[1]
                        if os >= 0x80:  # byte >= 128 → valor negativo
                            os -= 0x100
                        pc += 1
                        pc += os
                    case _:
                        debug(opc,[pc, ax, cx, dx, bx, sp, bp, si, di, flags])
            case _:
                debug(opc,[pc, ax, cx, dx, bx, sp, bp, si, di, flags])
                
                
        i+=1

    flags = (cf << 0) | (zf << 6) | (sf << 7) | (of << 11)

    # --- Actualizar argv ---
    argv[0] = (pc >> 8) & 0xFF
    argv[1] = pc & 0xFF
    argv[2] = (ax >> 8) & 0xFF
    argv[3] = ax & 0xFF
    argv[4] = (cx >> 8) & 0xFF
    argv[5] = cx & 0xFF
    argv[6] = (dx >> 8) & 0xFF
    argv[7] = dx & 0xFF
    argv[8] = (bx >> 8) & 0xFF
    argv[9] = bx & 0xFF
    argv[10] = (sp >> 8) & 0xFF
    argv[11] = sp & 0xFF
    argv[12] = (bp >> 8) & 0xFF
    argv[13] = bp & 0xFF
    argv[14] = (si >> 8) & 0xFF
    argv[15] = si & 0xFF
    argv[16] = (di >> 8) & 0xFF
    argv[17] = di & 0xFF
    argv[18] = flags & 0xFF

def debug(opc,regs):
    print("DEBUG:")
    sys.stdout.write("opcodes: ")
    for i in opc:
        sys.stdout.write(f"{i:02X} ")
    sys.stdout.write("\n")
    sys.stdout.flush()
    sr = ["IP", "AX", "CX", "DX", "BX", "SP", "DP", "SI", "DI", "F "]
    for i,j in zip(sr, regs):
        sys.stdout.write(
            f"{i} = {j:04X}" + "\n"
        )
    sys.exit(-1)