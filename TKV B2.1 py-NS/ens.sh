wine nasm.exe apps/main.asm -o C/main.bin
wine nasm.exe apps/cursor.asm -o C/cursor.bin -I apps/spr
wine nasm.exe apps/barr.asm -o C/barr.bin

echo "you need wine and nasm"
echo "/nasm <- in root"