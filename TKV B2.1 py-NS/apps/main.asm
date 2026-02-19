header:
    db "OA"
    db 00 ; v00
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
    mov ax, 0300H
    mov bx, 1
    mov di, _dbs_barr-_code
    syscall
    mov ax, 0300H
    mov bx, 1
    mov di, _dbs_cursor-_code
    syscall
    jmp $

_dbs:
    _dbs_cursor:
        db "cursor.bin", 0xFF
    _dbs_barr:
        db "barr.bin", 0xFF

_end: