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

    jmp _start

_dbs:
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
_end: