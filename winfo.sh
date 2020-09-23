#!/bin/sh

cd ~/kAFL/
python3 kAFL-Fuzzer/kafl_info.py \
	-vm_dir snapshot/ \
	-vm_ram snapshot/wram.qcow2 \
	-agent targets/windows_x86_64/bin/info/info.exe \
	-mem 4096 \
	-v \
	-work_dir out/
