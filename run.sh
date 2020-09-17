#!/bin/sh

# patch libxdc
#cd $HOME/kAFL/qemu-5.0.0/pt/
#cp $HOME/temp/libxdc/src/* .

# restore libxdc
#cd $HOME/kAFL/qemu-5.0.0/pt/
#cp $HOME/temp/pt/* .

cd $HOME/kAFL/
./install.sh qemu
./lfuzz.sh
