#!/bin/bash
set -e

# do make file? - I don't know.

echo "[ MAKE ] tmp/"
mkdir -p tmp mnt

# -----------------------------
# Crear imagen (64MB mejor que floppy)
# -----------------------------
echo "[ MAKE ] disk.img"
dd if=/dev/zero of=disk.img bs=1M count=64

# -----------------------------
# Crear partición
# -----------------------------
echo "[ FDISK ] disk.img"
echo -e "o\nn\np\n1\n\n\na\nw" | fdisk disk.img

# -----------------------------
# Loop device
# -----------------------------
echo "[ LOOP ] setup"
LOOP=$(sudo losetup -fP --show disk.img)
echo "Loop device: $LOOP"

# -----------------------------
# Formatear ext4
# -----------------------------
echo "[ MKFS ] ext4"
sudo mkfs.ext4 ${LOOP}p1

# -----------------------------
# Montar
# -----------------------------
echo "[ MOUNT ]"
sudo mount ${LOOP}p1 mnt

# -----------------------------
# Instalar GRUB
# -----------------------------
echo "[ GRUB ] install"
sudo grub-install --target=i386-pc --boot-directory=mnt/boot $LOOP

# -----------------------------
# Compilar kernel
# -----------------------------
echo "[ NASM ] kernel_entry.asm"
./nasm -f elf32 ./asm/kernel_entry.asm -o ./tmp/kernel_entry.o

echo "[ GCC ] kernel.c"
gcc -ffreestanding -m32 -fno-pie -c ./asm/kernel.c -o ./tmp/kernel.o

echo "[ LINK ] kernel ELF"
ld -m elf_i386 -T link.ld tmp/kernel_entry.o tmp/kernel.o -o tmp/kernel.elf

# -----------------------------
# Copiar kernel
# -----------------------------
echo "[ COPY ] kernel"
sudo cp ./tmp/kernel.elf mnt/boot/kernel.elf

# -----------------------------
# Config GRUB
# -----------------------------
echo "[ GRUB CFG ]"
sudo mkdir -p mnt/boot/grub

cat <<EOF | sudo tee mnt/boot/grub/grub.cfg
set timeout=0
set default=0

menuentry "Mi Kernel" {
    multiboot /boot/kernel.elf
    boot
}
EOF

# -----------------------------
# Desmontar
# -----------------------------
echo "[ UMOUNT ]"
sudo umount mnt
sudo losetup -d $LOOP

# -----------------------------
# Ejecutar
# -----------------------------
echo "[ RUN ]"
qemu-system-i386 -hda disk.img