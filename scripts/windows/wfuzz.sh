#!/bin/sh
cd ~/kAFL/
python3 kAFL-Fuzzer/kafl_fuzz.py \
	-vm_ram snapshot_win/ \
	-vm_dir snapshot_win/ \
	-agent targets/windows_x86_64/bin/fuzzer/bruteforce_test.exe \
	-mem 4096 \
	-seed_dir in/ \
	-work_dir out/ \
	-ip0 0xfffff80447aa0000-0xfffff80447ba5000 \
	-d \
	-v \
	--purge	-S windows
