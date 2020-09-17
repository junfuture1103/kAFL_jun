#!/bin/sh

cd ~/kAFL/
python3 kAFL-Fuzzer/kafl_info.py \
	-vm_dir snapshot/ \
	-vm_ram snapshot/ram.qcow2 \
	-agent targets/linux_x86_64/bin/info/info \
	-mem 512 \
	-v \
	-work_dir out/
