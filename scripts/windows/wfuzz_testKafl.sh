#!/bin/sh
cd ~/kAFL/
python3 kAFL-Fuzzer/kafl_fuzz.py \
	-vm_ram snapshot_win/ \
	-vm_dir snapshot_win/ \
	-agent targets/windows_x86_64/bin/fuzzer/hprintf_test.exe \
	-mem 4096 \
	-seed_dir in/ \
	-work_dir out/ \
	-ip0 0xfffff8011c610000-0xfffff8011c617000 \
	-d \
	-v \
	-tui \
	-graphic \
	-p 1 \
	--purge	-S windows
