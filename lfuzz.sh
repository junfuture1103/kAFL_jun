#!/bin/sh

cd ~/kAFL/
python3 kAFL-Fuzzer/kafl_fuzz.py \
	-vm_ram snapshot/ram.qcow2 \
	-vm_dir snapshot/ \
	-agent targets/linux_x86_64/bin/fuzzer/hprintf_test \
	-mem 512 \
	-seed_dir in/ \
	-work_dir out/ \
	-ip0 0xffffffffc029e000-0xffffffffc02a2000 \
	-d \
	-v --purge
