#!/bin/sh

sed -i '/qemu-5.0.0/c\qemu_kafl_location = '"$HOME"'/kAFL/qemu-5.0.0/x86_64-softmmu/qemu-system-x86_64' ~/kAFL/kAFL-Fuzzer/kafl.ini

mkdir ~/kAFL/snapshot
cd ~/kAFL/snapshot

~/kAFL/qemu-5.0.0/qemu-img create -b ~/kAFL/linux.qcow2 \
	-f qcow2 overlay_0.qcow2
~/kAFL/qemu-5.0.0/qemu-img create -f qcow2 ram.qcow2 512

cd ~/kAFL
mkdir out/
~/kAFL/qemu-5.0.0/x86_64-softmmu/qemu-system-x86_64 \
	-hdb ~/kAFL/snapshot/ram.qcow2 \
	-hda ~/kAFL/snapshot/overlay_0.qcow2 \
	-machine q35 -serial mon:stdio -net none \
	-enable-kvm -m 512 \
