header:
    db "OA"
    db 00         ; v00
    dw prog_ram_start
    dw prog_ram_end - prog_ram_start

times 20H-($-$$) db 0

prog_ram_start:
    dw _start
    dw _dbs
    dw _dbs
    dw _end
prog_ram_end:

times 100H-($-$$) db 0

_code:

_start:

    ; dibujar barra y botón siempre
    mov ax, 0F02H
    mov bx, _dbs_barr-_code
    syscall

    mov ax, 0F02H
    mov bx, _dbs_button-_code
    syscall
    ; -------------------------------
    ; LEER ESTADO DEL MOUSE
    ; -------------------------------
    mov AX, 3303H
    syscall

    ; -------------------------------
    ; DETECTAR "Clic recién presionado"
    ; -------------------------------
    mov al, [_dbs_prev-_code]

    cmp bl, 1
    je .no_toggle
    cmp al, 0
    je .no_toggle

    ; toggle menú
    xor byte [_dbs_menu-_code], 1

.no_toggle:
    ; actualizar estado previo
    mov [_dbs_prev-_code], bl
    
    ; verificar si el menu esta actibo
    mov al, [_dbs_menu-_code]
    cmp al, 0
    je _start

    ; -------------------------------
    ; dibujar menú si abierto
    ; -------------------------------

    mov ax, 0F02H
    mov bx, _dbs_menu_draw-_code
    syscall
    jmp _start

_dbs:
    _dbs_prev:
        db 0       ; estado previo del botón
    _dbs_now:
        db 0       ; estado actual del botón
    _dbs_menu:
        db 0       ; estado del menú (0 cerrado, 1 abierto)
    _dbs_barr:
        dw 800
        dw 40
        dw 0
        dw 480-40
        db 0,255,0
    _dbs_button:
        dw 20
        dw 20
        dw 10
        dw 480-30
        db 0,0,100
    _dbs_menu_draw:
        dw 100
        dw 20
        dw 10
        dw 480-140
        db 0,0,255
_end: