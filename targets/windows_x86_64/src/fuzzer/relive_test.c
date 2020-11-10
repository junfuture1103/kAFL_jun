/*
This is the Prototype of bruteforce-fuzztesting automation code.
Designed in consideration of medcored project's all constraints.
*/
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "kafl_user.h"

#define CODE_MAX_LEN 43

typedef enum {false, true} bool;

typedef struct _kAFL_IRP {
    uint32_t ioctlCode;
    int32_t inputBufferMin;
    int32_t inputBufferMax;
    int32_t outputBufferSize;
} kAFL_IRP;

kAFL_IRP constraints[] = {
	{0xa3350404,0x10,0x10,0x10},
	{0xa3350408,0x10,0x10,0xffff},
	{0xa335040c,0x0,0xffff,0xffff},
	{0xa3350410,0x0,0xffff,0xffff},
	{0xa3350444,0x4,0x4,0xffff},
	{0xa3350424,0x0,0xffff,0xffff},
	{0xa3350414,0x1,0xffff,0xffff},
	{0xa3350418,0x0,0xffff,0xffff},
	{0xa335044c,0x4,0x4,0xffff},
	{0xa3350440,0x618,0x618,0xffff},
	{0xa3350448,0x4,0x4,0xffff},
	{0xa335041c,0x1,0xffff,0xffff},
	{0xa3350450,0x4,0x4,0xffff},
	{0xa3350420,0x4,0x4,0xffff},
	{0xa3350040,0x0,0xffff,0x10},
	{0xa3350018,0x1,0xffff,0xffff},
	{0xa3350008,0x0,0xffff,0xffff},
	{0xa3350020,0x4,0x4,0xffff},
	{0xa335004c,0x4,0x4,0xffff},
	{0xa335000c,0x4,0x4,0xffff},
	{0xa3350000,0x0,0xffff,0x328},
	{0xa3350028,0x8,0x8,0xffff},
	{0xa3350048,0x4,0x4,0xffff},
	{0xa3350024,0x4,0x4,0xffff},
	{0xa335001c,0x1,0xffff,0xffff},
	{0xa335002c,0x14,0x14,0x47e},
	{0xa3350034,0x1,0xffff,0xffff},
	{0xa3350014,0x1,0x3ff,0xffff},
	{0xa3350038,0x1,0xffff,0xffff},
	{0xa3350030,0x4,0x4,0xffff},
	{0xa3350050,0x1,0xffff,0xffff},
	{0xa3350004,0x0,0xffff,0xffff},
	{0xa3350044,0x1,0x1,0xffff},
	{0xa335003c,0x1,0xffff,0xffff},
	{0xacd2201c,0x0,0xffff,0xffff},
	{0xacd22018,0x0,0xffff,0xffff},
	{0xacd22004,0x0,0xffff,0xffff},
	{0xacd22020,0x0,0xffff,0xffff},
	{0xacd22014,0x0,0xffff,0xffff},
	{0xacd22010,0x0,0xffff,0xffff},
	{0xacd22008,0x0,0xffff,0xffff},
	{0xacd2200c,0xa,0xa,0xffff},
	{0xacd22024,0x0,0xffff,0xffff}
};

bool filter_payload(uint8_t* data, int32_t size, kAFL_IRP *decoded_buf) 
{
    uint8_t codeIndex = data[0];
    if (codeIndex > CODE_MAX_LEN)
        return false;
    decoded_buf->ioctlCode = constraints[codeIndex].ioctlCode;

    if (size < constraints[codeIndex].inputBufferMin + 1 || size > constraints[codeIndex].inputBufferMax + 1)
        return false;

    decoded_buf->outputBufferSize = constraints[codeIndex].outputBufferSize;
	return true;
}

int main(int argc, char** argv)
{
    kAFL_IRP decoded_buf;
    uint8_t outBuffer[0xffff];
    uint8_t buf[0xffff];
    kAFL_payload* payload_buffer = (kAFL_payload*)VirtualAlloc(0, PAYLOAD_SIZE, MEM_COMMIT, PAGE_READWRITE);
    memset(payload_buffer, 0xffff, PAYLOAD_SIZE);

    /* open vulnerable driver */
    HANDLE kafl_vuln_handle = NULL;
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

    /* this hypercall submits the current CR3 value */ 
    kAFL_hypercall(HYPERCALL_KAFL_GET_PAYLOAD, (UINT64)payload_buffer);

    /* submit the guest virtual address of the payload buffer */
    kAFL_hypercall(HYPERCALL_KAFL_SUBMIT_CR3, 0);

    while (1) {
        /* request new payload (blocking) */
        kAFL_hypercall(HYPERCALL_KAFL_NEXT_PAYLOAD, 0);

        bool filter_res = filter_payload(payload_buffer->data, payload_buffer->size, &decoded_buf);
        // if (filter_res == false)
        //     continue;

        memset(buf, 0x00, sizeof(buf));
        memcpy(buf, (const char *)&payload_buffer->data[1], payload_buffer->size - 1);
        for (int j = 0; j < payload_buffer->size - 1; j++) {
            if (buf[j] <= 0x20 || 0x7f <= buf[j]) {
                buf[j] = '.';
            }
        }
        hprintf("Injecting data... (code: 0x%x, payload: %s, size: %d)\n", decoded_buf.ioctlCode, buf, payload_buffer->size - 1);
        kAFL_hypercall(HYPERCALL_KAFL_ACQUIRE, 0);
        
        /* kernel fuzzing */
        DeviceIoControl(kafl_vuln_handle,
            decoded_buf.ioctlCode,
            (LPVOID)&payload_buffer->data,
            (DWORD)payload_buffer->size,
            NULL,
            0,
            NULL,
            NULL
        );

        /* inform fuzzer about finished fuzzing iteration */
        hprintf("Injection finished.\n");
        kAFL_hypercall(HYPERCALL_KAFL_RELEASE, 0);
    }

    return 0;
}