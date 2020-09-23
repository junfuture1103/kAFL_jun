#!/bin/sh

cd ~/kAFL/
python3 kAFL-Fuzzer/kafl_fuzz.py \
	-vm_ram snapshot/wram.qcow2 \
	-vm_dir snapshot/ \
	-agent targets/windows_x86_64/bin/fuzzer/hprintf_test.exe \
	-mem 4096 \
	-seed_dir in/ \
	-work_dir out/ \
	-ip0 0xfffff80302770000-0xfffff80302777000 \
	-d \
	-v --purge
