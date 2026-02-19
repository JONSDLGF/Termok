# "UTILS"

from PIL import Image
import struct
import argparse
import os

def extract_sprites_to_separate_bim(input_file, output_dir, sprite_width, sprite_height):
    # Abrir la imagen
    img = Image.open(input_file).convert('RGBA')
    img_width, img_height = img.size

    # Crear carpeta de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    sprite_count = 0

    # Recorrer sprites por filas y columnas
    for y in range(0, img_height, sprite_height):
        for x in range(0, img_width, sprite_width):
            # Recortar el sprite
            sprite = img.crop((x, y, x + sprite_width, y + sprite_height))
            output_file = os.path.join(output_dir, f"sprite_{sprite_count}.bim")
            
            # Guardar sprite en archivo BIM separado
            with open(output_file, 'wb') as f:
                for py in range(sprite_height):
                    for px in range(sprite_width):
                        r, g, b, a = sprite.getpixel((px, py))
                        f.write(struct.pack('BBBB', r, g, b, a))
            
            sprite_count += 1

    print(f"{sprite_count} sprites extraídos a la carpeta '{output_dir}' correctamente.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrae sprites de un PNG a archivos BIM separados de 32 bits.")
    parser.add_argument("--i", required=True, help="Archivo PNG de entrada")
    parser.add_argument("--o", required=True, help="Carpeta de salida para los archivos BIM")
    parser.add_argument("--sw", type=int, default=16, help="Ancho de cada sprite")
    parser.add_argument("--sh", type=int, default=16, help="Alto de cada sprite")
    
    args = parser.parse_args()
    
    extract_sprites_to_separate_bim(args.i, args.o, args.sw, args.sh)
