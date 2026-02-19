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

    jmp _start

_dbs:
    _dbs_x:
        dw 0
    _dbs_y:
        dw 0
_end: