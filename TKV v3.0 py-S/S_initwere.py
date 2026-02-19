# S_initwere - context loader

import H_cpu
import H_gpu
import H_IO
import S_kernel
import M_Gin

mem = bytearray(1024*1024) # MIB

gin = M_Gin
gin.start(600,600,"VME v1.0.0")
gin.create()

gpu = H_gpu
gpu.set(gin.render)
io  = H_IO
io.set(gin.event)

harwere = {
    0:gpu,
    1:io
}
cpu = H_cpu

# inicializacion de la cpu
cpu.init(harwere)

kernel = S_kernel
kernel.init(cpu, mem, "main.bin")
kernel.loadinitk()
kernel.S_kernel()