/*
This is the Prototype of bruteforce-fuzztesting automation code.
Designed for medcored.sys.
*/
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "kafl_user.h"

#define CODE_MAX_LEN 10

typedef enum {false, true} bool;

typedef struct _kAFL_IRP {
    uint32_t ioctlCode;
    int32_t inputBufferSize;
    int32_t outputBufferSize;
    uint8_t* payload;
} kAFL_IRP;


kAFL_IRP constraints[10] = {
    {0xa3350408, 0x10, 0xff, NULL},
    {0xa335040c, 0xff, 0xff, NULL},
    {0xa3350410, 0x0, 0x0, NULL},
    {0xa3350424, 0xff, 0xff, NULL},
    {0xa335041c, 0xff, 0xff, NULL},
    {0xa335044c, 0x4, 0xff, NULL},
    {0xa3350418, 0x0, 0x0, NULL},
    {0xa3350448, 0x4, 0xff, NULL},
    {0xa3350444, 0x4, 0xff, NULL},
    {0xa3350450, 0x4, 0xff, NULL}
};

bool decode_payload(uint8_t* data, int32_t size, kAFL_IRP *decoded_buf) 
{
    uint8_t cIndex = data[0];
    if (cIndex > CODE_MAX_LEN)
        return false;
    hprintf("cIndex: %d\n", cIndex);
    decoded_buf->ioctlCode = constraints[cIndex].ioctlCode;

    if (size < constraints[cIndex].inputBufferSize + 1)
        decoded_buf->inputBufferSize = size - 1;
    else
        decoded_buf->inputBufferSize = constraints[cIndex].inputBufferSize;

    if (decoded_buf->inputBufferSize != 0) 
        decoded_buf->payload = &data[1];
    else 
        decoded_buf->payload = NULL;

    decoded_buf->outputBufferSize = constraints[cIndex].outputBufferSize;

    return true;
}

int main(int argc, char** argv)
{
    kAFL_IRP decoded_buf;
    uint8_t outBuffer[0xff];
    uint8_t buf[0x1000];
    

    hprintf("Starting... %s\n", argv[0]);

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

    hprintf("Allocating buffer for kAFL_payload struct\n");
    kAFL_payload* payload_buffer = (kAFL_payload*)VirtualAlloc(0, PAYLOAD_SIZE, MEM_COMMIT, PAGE_READWRITE);

    hprintf("Memset kAFL_payload at address %lx (size %d)\n", (uint64_t) payload_buffer, PAYLOAD_SIZE);
    memset(payload_buffer, 0xff, PAYLOAD_SIZE);

    /* submit the guest virtual address of the payload buffer */
    hprintf("Submitting buffer address to hypervisor...\n");
    kAFL_hypercall(HYPERCALL_KAFL_GET_PAYLOAD, (UINT64)payload_buffer);

    /* this hypercall submits the current CR3 value */
    hprintf("Submitting current CR3 value to hypervisor...\n");
    kAFL_hypercall(HYPERCALL_KAFL_SUBMIT_CR3, 0);

    while (1) {
        /* request new payload (blocking) */
        kAFL_hypercall(HYPERCALL_KAFL_NEXT_PAYLOAD, 0);
        
        memset(buf, 0x00, sizeof(buf));
        memcpy(buf, (const char *)payload_buffer->data, payload_buffer->size);
        for (int i = 0; i < payload_buffer->size; i++) {
            if (buf[i] <= 0x20 || 0x7f <= buf[i]) {
                buf[i] = '.';
            }
        }
        hprintf("origianl payload: %s, original size: %d\n", buf, payload_buffer->size);

        bool is_decoded = decode_payload(payload_buffer->data, payload_buffer->size, &decoded_buf);
        if (is_decoded == false)
            continue;

        memset(buf, 0x00, sizeof(buf));
        memcpy(buf, (const char *)decoded_buf.payload, decoded_buf.inputBufferSize);
        for (int j = 0; j < decoded_buf.inputBufferSize; j++) {
            if (buf[j] <= 0x20 || 0x7f <= buf[j]) {
                buf[j] = '.';
            }
        }

        /* kernel fuzzing */
        hprintf("Injecting data... (payload: %s, size: %d)\n", buf, decoded_buf.inputBufferSize);
        kAFL_hypercall(HYPERCALL_KAFL_ACQUIRE, 0);
        /* kernel fuzzing */
        DeviceIoControl(kafl_vuln_handle,
            decoded_buf.ioctlCode,
            (LPVOID)decoded_buf.payload,
            (DWORD)decoded_buf.inputBufferSize,
            (LPVOID)outBuffer,
            (DWORD)decoded_buf.outputBufferSize,
            NULL,
            NULL
        );

        /* inform fuzzer about finished fuzzing iteration */
        hprintf("Injection finished.\n");
        kAFL_hypercall(HYPERCALL_KAFL_RELEASE, 0);
    }

    return 0;
}