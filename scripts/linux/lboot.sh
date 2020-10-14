#!/bin/sh

cd ~/kAFL/
~/kAFL/qemu-5.0.0/x86_64-softmmu/qemu-system-x86_64 \
	-machine q35 -cpu host -enable-kvm -m 512 \
	-hda linux.qcow2 -cdrom ~/ubuntu.iso -usbdevice tablet
