header:
    db "OA"
    db 0
    dw prog_ram_start
    dw prog_ram_end - prog_ram_start

times 20H-($-$$) db 0

prog_ram_start:
    dw _start
    dw _dbs
    dw _image
    dw _end
prog_ram_end:

times 100H-($-$$) db 0

_code:

_start:
    mov AX, 3300H      ; INT 33h, subcall 0 = establecer estado
    syscall

main_loop:

    ; --- leer mouse ---
    mov AX, 3303H      ; INT 33h, subcall 3 = leer estado
    syscall
    ; Ahora:
    ; BX = botones, CX = X, DX = Y
    ; Si botón izquierdo presionado

    CMP BX, 1
    je click
    jne no_click

    click:
        mov AX, 0F04H
        mov BX, _image_on_click-_code
        syscall
        jmp main_loop

    no_click:
        mov AX, 0F04H
        mov BX, _image_off_click-_code
        syscall
        jmp main_loop

    jmp main_loop

_dbs:

_image:
    _image_off_click:
        dw 0010H
        dw 0010H
        incbin "off_click.bim"
    _image_on_click:
        dw 0010H
        dw 0010H
        incbin "on_click.bim"

_end: