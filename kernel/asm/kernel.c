// 32 bits gcc
// version: 0.1-experiment

// kernel.c
void kmain(void);


#include <stdint.h>
const uint8_t width = 80;
const uint8_t height = 25;

// video
volatile unsigned short * const video = (unsigned short*)0xB8000;

void clear_all() {
    for(volatile int x=0; x<2000; x++){
        // Limpiar posición anterior
        video[x] = (0x0F << 8) | ' '; // blanco sobre negro
    }
}

// kernel.c
void kmain(void) {
    clear_all();

    // Animación: mover un X en la pantalla
    int x = 0, y = 10;
    int direction = 1; // 1 = derecha, -1 = izquierda

    while(1) {
        // Limpiar posición anterior
        video[y * width + x] = (0x0F << 8) | ' '; // blanco sobre negro

        // Actualizar posición
        x += direction;
        if (x >= width-1) direction = -1;
        if (x <= 0) direction = 1;

        // Dibujar X en nueva posición con color rojo
        video[y * width + x] = (0x4C << 8) | 'X';

        // Retraso simple (bucle ocupado)
        for (volatile int delay=0; delay<20000000; delay++);
    }
}