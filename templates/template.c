#include <windows.h>
#include <stdio.h>
#include "kafl_user.h"

DWORD ioctl_code[__NUM_CODE__] = { 0 };

int main(int argc, char** argv)
{
    kAFL_payload* payload_buffer = (kAFL_payload*)VirtualAlloc(0, PAYLOAD_SIZE, MEM_COMMIT, PAGE_READWRITE);
    int i;

    memset(payload_buffer, 0xff, PAYLOAD_SIZE);

    /* open vulnerable driver */
    HANDLE kafl_vuln_handle = NULL;
    BOOL status = -1;
    kafl_vuln_handle = CreateFile((LPCSTR)"\\\\.\\__SVCNAME__",
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED,
        NULL
    );

    if (kafl_vuln_handle == INVALID_HANDLE_VALUE) {
        printf("cannot get device handle: 0x%x\n", GetLastError());
        ExitProcess(0);
    }

    /* this hypercall submits the current CR3 value */ 
    kAFL_hypercall(HYPERCALL_KAFL_SUBMIT_CR3, 0);

    /* submit the guest virtual address of the payload buffer */
    kAFL_hypercall(HYPERCALL_KAFL_GET_PAYLOAD, (UINT64)payload_buffer);

    /* INITIALIZE ioctl_code HERE */

    for (i = 0; i < __NUM_CODE__; i++) {
        while (__ITERS__) {
            /* request new payload (blocking) */
            kAFL_hypercall(HYPERCALL_KAFL_NEXT_PAYLOAD, 0);
            kAFL_hypercall(HYPERCALL_KAFL_ACQUIRE, 0);
            /* kernel fuzzing */
            DeviceIoControl(kafl_vuln_handle,
                ioctl_code[i],
                (LPVOID)(payload_buffer->data),
                (DWORD)payload_buffer->size,
                NULL,
                0,
                NULL,
                NULL
            );
            /* inform fuzzer about finished fuzzing iteration */
            kAFL_hypercall(HYPERCALL_KAFL_RELEASE, 0);
        }
    }
    return 0;
}

