/*
This is the Prototype of bruteforce-fuzztesting automation code.
Designed for medcored.sys.
*/
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "kafl_user.h"

typedef enum {false, true} bool;

typedef struct _kAFL_decoded {
    DWORD ioctlCode;
    int32_t inputBuffersize;
    int32_t outputBuffersize;
    uint8_t* payload;
} kAFL_decoded;

typedef struct _Constraint {
    DWORD ioctl_code;
    int32_t inputBufferLength;
    int32_t outputBufferLength;
    bool is_static;
} Constraint;

Constraint constraints[10] = {
    {0xa3350404, 0x10, 0x10, true},
    {0xa3350408, 0x10, 0x30, true},
    {0xa335040c, 0x20, 0x30, false},
    {0xa3350410, 0x0, 0x0, true},
    {0xa3350424, 0x10, 0x30, false},
    {0xa335041c, 0x10, 0x30, false},
    {0xa3350414, 0x20, 0x30, false},
    {0xa335044c, 0x4, 0x30, true},
    {0xa3350418, 0x0, 0x0, true},
    {0xa3350448, 0x4, 0x30, true}
};

int32_t payload_decode(uint8_t* data, int32_t size, kAFL_decoded decoded_buf[]) 
{
    /*
    Constraints code, input output static
    */
    int32_t cIndex;
    int32_t decoded_len = 0;
    for (int i = 0; i < size && decoded_len < 0x20;) {
        cIndex = atoi((char*)&data[i]);
        decoded_buf[decoded_len].ioctlCode = constraints[cIndex].ioctl_code;
        
        if (size < i + constraints[cIndex].inputBufferLength + 1)
            decoded_buf[decoded_len].inputBuffersize = size - i - 1;
        else
            decoded_buf[decoded_len].inputBuffersize = constraints[cIndex].inputBufferLength;

        if (decoded_buf[decoded_len].inputBuffersize != 0) 
            decoded_buf[decoded_len].payload = &data[++i];
        else 
            decoded_buf[decoded_len].payload = NULL;
        
        decoded_buf[decoded_len].outputBuffersize = constraints[cIndex].outputBufferLength;
        i += decoded_buf[decoded_len].inputBuffersize + 1;
        decoded_len++;
    }
    return decoded_len;
}

int main(int argc, char** argv)
{
    kAFL_decoded decoded_buf[0x20];

    uint8_t outBuffer[0x10];

    hprintf("Starting... %s\n", argv[0]);

    hprintf("Allocating buffer for kAFL_payload struct\n");
    kAFL_payload* payload_buffer = (kAFL_payload*)VirtualAlloc(0, PAYLOAD_SIZE, MEM_COMMIT, PAGE_READWRITE);

    hprintf("Memset kAFL_payload at address %lx (size %d)\n", (uint64_t) payload_buffer, PAYLOAD_SIZE);
    memset(payload_buffer, 0xff, PAYLOAD_SIZE);

    /* open vulnerable driver */
    HANDLE kafl_vuln_handle = NULL;
    hprintf("Attempting to open vulnerable device file (%s)\n", "\\\\.\\medcored");
    kafl_vuln_handle = CreateFile((LPCSTR)"\\\\.\\medcored",
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED,
        NULL
    );

    if (kafl_vuln_handle == INVALID_HANDLE_VALUE) {
        hprintf("[-] Cannot get device handle: 0x%X\n", GetLastError());
        ExitProcess(0); 
    }

    /* submit the guest virtual address of the payload buffer */
    hprintf("Submitting buffer address to hypervisor...\n");
    kAFL_hypercall(HYPERCALL_KAFL_GET_PAYLOAD, (UINT64)payload_buffer);

    /* this hypercall submits the current CR3 value */
    hprintf("Submitting current CR3 value to hypervisor...\n");
    kAFL_hypercall(HYPERCALL_KAFL_SUBMIT_CR3, 0);

    while (1) {
        /* request new payload (blocking) */
        kAFL_hypercall(HYPERCALL_KAFL_NEXT_PAYLOAD, 0);
        int32_t decoded_len = payload_decode(payload_buffer->data, payload_buffer->size, decoded_buf);

        kAFL_hypercall(HYPERCALL_KAFL_ACQUIRE, 0);
        
        for (int i = 0; i < decoded_len; i++) {
        /* kernel fuzzing */
        DeviceIoControl(kafl_vuln_handle,
            decoded_buf[decoded_len].ioctlCode,
            (LPVOID)decoded_buf[i].payload,
            (DWORD)decoded_buf[i].inputBuffersize,
            (LPVOID)outBuffer,
            (DWORD)decoded_buf[i].outputBuffersize,
            NULL,
            NULL
        );

        /* inform fuzzer about finished fuzzing iteration */
        hprintf("Injection finished.\n");
        kAFL_hypercall(HYPERCALL_KAFL_RELEASE, 0);
        }   
    }

    return 0;
}
