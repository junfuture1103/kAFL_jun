#!/bin/sh
cd ~/kAFL/
python3 kAFL-Fuzzer/kafl_fuzz.py \
	-vm_ram snapshot_win/wram.qcow2 \
	-vm_dir snapshot_win/ \
	-agent targets/windows_x86_64/bin/fuzzer/ssport_test.exe \
	-mem 4096 \
	-seed_dir in/ \
	-work_dir out/ \
<<<<<<< HEAD
	-ip0 0xfffff8061b060000-0xfffff8061b068000 \
=======
	-ip0 0xfffff80320f20000-0xfffff80320f27000 \
>>>>>>> gnbon-develop
	-d \
	-v \
	-S windows \
	--purge
