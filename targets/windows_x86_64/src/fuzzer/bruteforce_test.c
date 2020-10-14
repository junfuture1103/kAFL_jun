#include <windows.h>
#include <stdio.h>
#include <stdint.h>
#include "kafl_user.h"

typedef struct _kAFL_decoded{
    DWORD code;
    int32_t size;
    uint8_t* payload;
} kAFL_decoded;

DWORD ioctl_code[] = {0xa0006810, 0xa0006814, 0xa0006818, 0xa000e804};
int32_t ioctl_size[] = {8, 0, 0, 4};

int32_t payload_decode(kAFL_decoded decoded_buf, uint8_t* data, int32_t size) 
{
    int32_t decoded_len = 0;
    for (int i = 0; i < size || decoded_len < 4;) {
        decoded_buf[decoded_len].code = ioctl_code[data[i]];
        
        if (size < i + ioctl_size[data[i]] + 1)
            decoded_buf[decoded_len].size = size - i - 1;
        else
            decoded_buf[decoded_len].size = ioctl_size[data[i]];

        if (decoded_buf[decoded_len].size != 0) 
            decoded_buf[decoded_len].payload = &data[++i];
        else 
            decoded_buf[decoded_len].payload = NULL;
        
        i += decoded_buf[decoded_len].size + 1;
        decoded_len++;
    }
    return decoded_len;
}

int main(int argc, char** argv)
{
    kAFL_decoded decoded_buf[4];
    uint8_t outBuffer[0x48];
    
    kAFL_payload* payload_buffer = (kAFL_payload*)VirtualAlloc(0, PAYLOAD_SIZE, MEM_COMMIT, PAGE_READWRITE);

    memset(payload_buffer, 0xff, PAYLOAD_SIZE);

    /* open vulnerable driver */
    HANDLE kafl_vuln_handle = NULL;
    BOOL status = -1;
    kafl_vuln_handle = CreateFile((LPCSTR)"\\\\.\\\\AswVmm",
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

    while () {
        /* request new payload (blocking) */
        kAFL_hypercall(HYPERCALL_KAFL_NEXT_PAYLOAD, 0);
        int32_t decoded_len = payload_decode(decoded_buf, payload_buffer->data, payload_buffer->size);

        kAFL_hypercall(HYPERCALL_KAFL_ACQUIRE, 0);
        
        for (i = 0; i < decoded_len; i++) {
        /* kernel fuzzing */
        DeviceIoControl(kafl_vuln_handle,
            decoded_buf[decoded_len].code,
            (LPVOID)decoded_buf[i].payload,
            (DWORD)decoded_buf[i].size,
            (LPVOID)outBuffer,
            (DWORD)sizeof(outBuffer),
            NULL,
            NULL
        );

        /* inform fuzzer about finished fuzzing iteration */
        kAFL_hypercall(HYPERCALL_KAFL_RELEASE, 0);
        }   
    }

    return 0;
}