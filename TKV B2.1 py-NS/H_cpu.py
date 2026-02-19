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

def alu(oper, bits, a, b, cf, pf, zf, sf, of):
    mask = (1 << bits) - 1
    sign = 1 << (bits - 1)

    # --- Helpers ---
    def set_flags(result, carry, overflow):
        cf = carry
        pf = 1 if bin(result & 0xFF).count("1") % 2 == 0 else 0
        zf = 1 if (result & mask) == 0 else 0
        sf = 1 if (result & sign) != 0 else 0
        of = overflow
        return cf, pf, zf, sf, of

    # ========================
    #       ADD
    # ========================
    if oper == 0b0000:
        result = (a + b) & mask
        carry = 1 if (a + b) > mask else 0
        overflow = 1 if (~(a ^ b) & (a ^ result) & sign) else 0
        cf, pf, zf, sf, of = set_flags(result, carry, overflow)
        return result, b, cf, pf, zf, sf, of

    # ========================
    #       OR
    # ========================
    if oper == 0b0001:
        result = a | b
        cf, pf, zf, sf, of = set_flags(result, 0, 0)
        return result & mask, b, cf, pf, zf, sf, of

    # ========================
    #       AND
    # ========================
    if oper == 0b0100:
        result = a & b
        cf, pf, zf, sf, of = set_flags(result, 0, 0)
        return result & mask, b, cf, pf, zf, sf, of

    # ========================
    #       SUB
    # ========================
    if oper == 0b0101:
        result = (a - b) & mask
        carry = 1 if a < b else 0
        overflow = 1 if ((a ^ b) & (a ^ result) & sign) else 0
        cf, pf, zf, sf, of = set_flags(result, carry, overflow)
        return result, b, cf, pf, zf, sf, of

    # ========================
    #       XOR
    # ========================
    if oper == 0b0110:
        result = a ^ b
        cf, pf, zf, sf, of = set_flags(result, 0, 0)
        return result & mask, b, cf, pf, zf, sf, of

    # ========================
    #       CMP
    # ========================
    if oper == 0b0111:
        result = (a - b) & mask
        carry = 1 if a < b else 0
        overflow = 1 if ((a ^ b) & (a ^ result) & sign) else 0
        cf, pf, zf, sf, of = set_flags(result, carry, overflow)
        return a, b, cf, pf, zf, sf, of

    # ========================
    #       INC
    # ========================
    if oper == 0b1000:
        result = (a + 1) & mask
        overflow = 1 if ((a & sign) == 0 and (result & sign) != 0) else 0
        _, pf, zf, sf, of = set_flags(result, cf, overflow)
        return result, b, cf, pf, zf, sf, of

    # ========================
    #       DEC
    # ========================
    if oper == 0b1001:
        result = (a - 1) & mask
        overflow = 1 if ((a & sign) != 0 and (result & sign) == 0) else 0
        _, pf, zf, sf, of = set_flags(result, cf, overflow)
        return result, b, cf, pf, zf, sf, of

    raise ValueError(f"Operación ALU desconocida: {oper}")

def MR(mem, reg, load=None):

    def isreg(name):
        return isinstance(reg, str) and reg == name

    # =========================
    # LECTURA
    # =========================
    if load is None:

        # ---- AX ----
        if reg == 0 or isreg("AX"):
            return (mem[2] << 8) | mem[3]
        if isreg("AH"):
            return mem[2]
        if isreg("AL"):
            return mem[3]

        # ---- CX ----
        if reg == 1 or isreg("CX"):
            return (mem[4] << 8) | mem[5]
        if isreg("CH"):
            return mem[4]
        if isreg("CL"):
            return mem[5]

        # ---- DX ----
        if reg == 2 or isreg("DX"):
            return (mem[6] << 8) | mem[7]
        if isreg("DH"):
            return mem[6]
        if isreg("DL"):
            return mem[7]

        # ---- BX ----
        if reg == 3 or isreg("BX"):
            return (mem[8] << 8) | mem[9]
        if isreg("BH"):
            return mem[8]
        if isreg("BL"):
            return mem[9]

        # ---- SP BP SI DI ----
        if reg == 4 or isreg("SP"):
            return (mem[10] << 8) | mem[11]
        if reg == 5 or isreg("BP"):
            return (mem[12] << 8) | mem[13]
        if reg == 6 or isreg("SI"):
            return (mem[14] << 8) | mem[15]
        if reg == 7 or isreg("DI"):
            return (mem[16] << 8) | mem[17]

        # ---- IP ----
        if reg == 8 or isreg("IP"):
            return (mem[0] << 8) | mem[1]

        if isreg("IP++"):
            ip = (mem[0] << 8) | mem[1]
            ip = (ip + 1) & 0xFFFF
            mem[0] = (ip >> 8) & 0xFF
            mem[1] = ip & 0xFF
            return ip

        # ---- FLAGS ----
        if reg == 9 or isreg("F"):
            return mem[18]

        return "ERR"

    # =========================
    # ESCRITURA
    # =========================
    else:

        load &= 0xFFFF

        # ---- AX ----
        if reg == 0 or isreg("AX"):
            mem[2] = (load >> 8) & 0xFF
            mem[3] = load & 0xFF
        elif isreg("AH"):
            mem[2] = load & 0xFF
        elif isreg("AL"):
            mem[3] = load & 0xFF

        # ---- CX ----
        elif reg == 1 or isreg("CX"):
            mem[4] = (load >> 8) & 0xFF
            mem[5] = load & 0xFF
        elif isreg("CH"):
            mem[4] = load & 0xFF
        elif isreg("CL"):
            mem[5] = load & 0xFF

        # ---- DX ----
        elif reg == 2 or isreg("DX"):
            mem[6] = (load >> 8) & 0xFF
            mem[7] = load & 0xFF
        elif isreg("DH"):
            mem[6] = load & 0xFF
        elif isreg("DL"):
            mem[7] = load & 0xFF

        # ---- BX ----
        elif reg == 3 or isreg("BX"):
            mem[8] = (load >> 8) & 0xFF
            mem[9] = load & 0xFF
        elif isreg("BH"):
            mem[8] = load & 0xFF
        elif isreg("BL"):
            mem[9] = load & 0xFF

        # ---- SP BP SI DI ----
        elif reg == 4 or isreg("SP"):
            mem[10] = (load >> 8) & 0xFF
            mem[11] = load & 0xFF
        elif reg == 5 or isreg("BP"):
            mem[12] = (load >> 8) & 0xFF
            mem[13] = load & 0xFF
        elif reg == 6 or isreg("SI"):
            mem[14] = (load >> 8) & 0xFF
            mem[15] = load & 0xFF
        elif reg == 7 or isreg("DI"):
            mem[16] = (load >> 8) & 0xFF
            mem[17] = load & 0xFF

        # ---- IP ----
        elif reg == 8 or isreg("IP"):
            mem[0] = (load >> 8) & 0xFF
            mem[1] = load & 0xFF

        elif isreg("IP++"):
            load = (load + 1) & 0xFFFF
            mem[0] = (load >> 8) & 0xFF
            mem[1] = load & 0xFF

        # ---- FLAGS ----
        elif reg == 9 or isreg("F"):
            mem[18] = load & 0xFF

        else:
            return "ERR"

        return None

# --- CPU virtual completo NO ---
def cpu(ring, argv, mem, sect, calls, steps=16):
    flags = MR(argv, "F")

    cf = (flags>> 0)&1
    pf = (flags>> 2)&1
    zf = (flags>> 6)&1
    sf = (flags>> 7)&1
    of = (flags>>11)&1

    i = 0
    while i < steps:
        # --- verificación de ejecución ---
        global_pc = MMU(sect, MR(argv, "IP"), 0b001)
        if global_pc == -1 and ring == 1:
            calls(regs=[0, 0, 0, 0, 0, 0])
            return -2
        
        opc=mem[global_pc:global_pc+16]

        MR(argv, "IP++")
        match opc[0]>>4:
            case 0x0:
                match opc[0]&0xF:
                    case 0xF:
                        if opc[1]==0x05:
                            e = calls([
                                MR(argv, "AX"),
                                MR(argv, "BX"),
                                MR(argv, "CX"),
                                MR(argv, "DX"),
                                MR(argv, "SI"),
                                MR(argv, "DI")])
                            if isinstance(e,int):
                                return -1
                            MR(argv, "AX", e[0])
                            MR(argv, "BX", e[1])
                            MR(argv, "CX", e[2])
                            MR(argv, "DX", e[3])
                            MR(argv, "SI", e[4])
                            MR(argv, "DI", e[5])
                            MR(argv, "IP++")
                    case _:
                        debug(opc,argv)
            case 0x7:  # Jcc rel8
                opcode = opc[0]
                rel8 = opc[1]

                # signo correcto
                if rel8 & 0x80:
                    rel8 -= 0x100

                ip = MR(argv, "IP")
                next_ip = ip + 1

                cond = opcode & 0x0F
                take = False

                match cond:
                    case 0x0: take = of == 1               # JO
                    case 0x1: take = of == 0               # JNO
                    case 0x2: take = cf == 1               # JB / JC
                    case 0x3: take = cf == 0               # JNB
                    case 0x4: take = zf == 1               # JZ
                    case 0x5: take = zf == 0               # JNZ
                    case 0x6: take = cf == 1 or  zf == 1   # JBE
                    case 0x7: take = cf == 0 and zf == 0   # JA
                    case 0x8: take = sf == 1               # JS
                    case 0x9: take = sf == 0               # JNS
                    case 0xA: take = pf == 1               # JP
                    case 0xB: take = pf == 0               # JNP
                    case 0xC: take = sf != of              # JL
                    case 0xD: take = sf == of              # JGE
                    case 0xE: take = zf == 1 or  sf !=  of # JLE
                    case 0xF: take = zf == 0 and sf ==  of # JG
                    case _: debug(opc, argv)

                if take:
                    MR(argv, "IP", next_ip + rel8)
                else:
                    MR(argv, "IP", next_ip)
            case 0x8:
                match opc[0]&0xF:
                    case 3:
                        mod = (opc[1]&0b11_000_000)>>6
                        ope = (opc[1]&0b00_111_000)>>3
                        reg = (opc[1]&0b00_000_111)>>0
                        MR(argv, "IP++")
                        imm8 = opc[2]
                        MR(argv, "IP++")
                        if mod==0b11:
                            ret, _, cf, pf, zf, sf, of = alu(ope, 16, MR(argv, reg), imm8, cf, pf, zf, sf, of)
                            MR(argv, reg, ret)
                    case _:
                        debug(opc,argv)
            case 0xA:
                match opc[0]&0xF:
                    case 0:
                        os   = opc[2]
                        MR(argv, "IP++")
                        os <<= 8
                        os  |= opc[1]
                        MR(argv, "IP++")

                        global_pc = MMU(sect, os, 0b100)
                        if global_pc == -1 and ring == 1:
                            return -2
                        
                        MR(argv, "AL", mem[global_pc])
                    case _:
                        debug(opc,argv)
            case 0xB:
                if (opc[0]&0xF) >= 0x8: # MOV AX-DI, imm16
                    reg = opc[0]&0x7
                    MR(argv, reg, opc[2])
                    MR(argv, "IP++")
                    MR(argv, reg, MR(argv, reg) << 8)
                    MR(argv, reg, MR(argv, reg) | opc[1])
                    MR(argv, "IP++")
                else:
                    debug(opc,argv)
            case 0xE:
                match opc[0]&0xF:
                    case 0xB:
                        os = opc[1]
                        MR(argv, "IP++")
                        if os >= 0x80:  # byte >= 128 → valor negativo
                            os -= 0x100
                        MR(argv, "IP", MR(argv, "IP")+os)
                    case _:
                        debug(opc,argv)
            case _:
                debug(opc,argv)
        i+=1

    flags = (
        (cf << 0)  |   # Carry
        (1  << 1)  |   # bit fijo a 1
        (pf << 2)  |   # Parity
        (zf << 6)  |   # Zero
        (sf << 7)  |   # Sign
        (of << 11)     # Overflow
    )

    # --- Actualizar argv ---
    MR(argv, "F", flags)

def debug(opc,regs):
    print("DEBUG:")
    sys.stdout.write("opcodes: ")
    for i in opc:
        sys.stdout.write(f"{i:02X} ")
    sys.stdout.write("\n")
    sys.stdout.flush()
    sr = ["IP", "AX", "CX", "DX", "BX", "SP", "BP", "SI", "DI", "F"]
    for i in zip(sr):
        sys.stdout.write(
            f"{i[0]} = {MR(regs,i[0]):04X}" + "\n"
        )
    sys.stdout.flush()
    sys.exit(-1)
