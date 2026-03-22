create date: 27 nov 2025
version: 0.1-experimental
name: Termok

kernel:
    bits: now only 32, "64"
    code version: 0.1-experimental

filosofy:
    en-EN: Everything is a compressed or formatted file and is introspective.
    es-ES: todo es un archivo comprimido o con formato y es introspecciónable.

compiler depends:
    nasm

virtual machine:
    ./TKV ( termok virtual-machine ) v3.1
    headerfile:
        header:
            # by: <name>
            # file: <name:__file__>
            # type: 'do the script'
            # LIC: "/licens/<name>"
        coment:
            "<type>" -> "UTILS" not inportant

    libs:
        sys
        pathlib
        copy
        ctypes
        pip:
            sdl2
            <numpy:cupy>