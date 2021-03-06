if [[ "$OSTYPE" == "linux-gnu" ]]; then

	mkdir bin/ 2> /dev/null
	mkdir bin/loader/ 2> /dev/null
	mkdir bin/fuzzer/ 2> /dev/null
	mkdir bin/info/ 2> /dev/null

	if x86_64-w64-mingw32-gcc -v 2> /dev/null && x86_64-w64-mingw32-g++ -v 2> /dev/null; then
		printf "\tCompiling loader...\n"
		x86_64-w64-mingw32-g++ src/info/info.cpp -I ../ -o bin/info/info.exe -lntdll -lpsapi
		printf "\tCompiling info executable...\n"
		x86_64-w64-mingw32-gcc src/loader/loader.c -I ../ -o bin/loader/loader.exe -Wall -lpsapi
		printf "\tCompiling vuln_driver fuzzer...\n"
		x86_64-w64-mingw32-gcc src/fuzzer/vuln_test.c -I ../ -o bin/fuzzer/vuln_test.exe
        printf "\tCompiling hprintf test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/hprintf_test.c -I ../ -o bin/fuzzer/hprintf_test.exe -mwindows -Wall
		printf "\tCompiling bruteforcing_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/bruteforce_test.c -I ../ -o bin/fuzzer/bruteforce_test.exe -mwindows -Wall
		printf "\tCompiling relive_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/relive_test.c -I ../ -o bin/fuzzer/relive_test.exe -mwindows -Wall
		printf "\tCompiling medcored_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/medcored_test.c -I ../ -o bin/fuzzer/medcored_test.exe -mwindows -Wall
		printf "\tCompiling aswVmm_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/aswVmm_test.c -I ../ -o bin/fuzzer/aswVmm_test.exe -mwindows -Wall
		printf "\tCompiling cng_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/cng_test.c -I ../ -o bin/fuzzer/cng_test.exe -mwindows -Wall
		printf "\tCompiling MsIo_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/MsIo_test.c -I ../ -o bin/fuzzer/MsIo_test.exe -mwindows -Wall
		printf "\tCompiling input_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/input_test.c -I ../ -o bin/fuzzer/input_test.exe -mwindows -Wall
		printf "\tCompiling Spark_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/Spark_test.c -I ../ -o bin/fuzzer/Spark_test.exe -mwindows -Wall
		printf "\tCompiling pdicIo_test...\n"
        x86_64-w64-mingw32-gcc src/fuzzer/pdicIo_test.c -I ../ -o bin/fuzzer/pdicIo_test.exe -mwindows -Wall

	else
	printf "\tCould not find x86_64-w64-mingw32-gcc/g++! Skipping..\n\t(Try sudo apt install gcc-mingw-w64-x86-64 g++-mingw-w64-x86-64 to fix this)"
	fi 
else
	printf "\tError: Need to run Linux to compile these components! Skipping..!\n"
fi


# sudo apt install gcc-mingw-w64-x86-64
# sudo apt install gcc-mingw-w64-x86-64
# linux_x86-64-2$ x86_64-w64-mingw32-gcc -v
