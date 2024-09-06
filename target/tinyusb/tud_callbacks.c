#include "class/cdc/cdc_device.h"
#include "tinyusb/tud_callbacks.h"
#include "tusb.h"

// TODO: move operations to handler/loop instead of callback (?)
// not sure if this matters since tusb is already running tasks in a loop

extern uint8_t* image_buffer_addr;

// TODO: move elsewhere
enum commands {
    CMD_BUF_RESET = 0,
    CMD_BUF_SET_ADDR,
    CMD_BUF_SET_DATA,
    CMD_BUF_CHECKSUM,
    CMD_PANEL_REFRESH,
    CMD_SYS_RESTART,
    CMD_SYS_BOOTLOADER,
    NUM_COMMANDS,
};

void print_buf(uint8_t const* buffer, uint16_t bufsize) {
    // printf("buf[%d]: ", bufsize);
    for (int i=0; i<bufsize; i++) {
        if (i % 8 == 0) printf("\n");
        printf("0x%02x ", buffer[i]);
    }
    printf("\n");
}

uint16_t tud_hid_get_report_cb(uint8_t itf, uint8_t report_id, hid_report_type_t report_type, uint8_t* buffer, uint16_t reqlen) {
    return 0;
}

void tud_hid_set_report_cb(uint8_t itf, uint8_t report_id, hid_report_type_t report_type, uint8_t const* buffer, uint16_t bufsize) {
    static uint32_t buffer_index = 0;
    static uint16_t packet_index = 0;
    uint32_t data_length = 0;

    // TODO: check length, incl. max length + commands
    // TODO: bounds checks
    switch (buffer[0]) {
    case CMD_BUF_RESET:
        // TODO: can use DMA with INCR_READ = 0
        printf("resetting buffer\n");
        buffer_index = 0;
        packet_index = 0;
        break;

    case CMD_BUF_SET_ADDR:
        // LSB FIRST, 12 bits
        buffer_index = (buffer[1] | (buffer[2] << 8) | buffer[3] << 16); 
        printf("set addr: 0x%x (%d)\n", buffer_index, buffer_index);
        packet_index = 0;
        break;

    case CMD_BUF_SET_DATA:
        data_length = bufsize - 1;

        printf("data_buffer (packet=%d, len=%d): ", packet_index, data_length);
        print_buf(&buffer[1], data_length);

        // TODO: DMA! does the buffer go out of scope?
        // TODO: check buffer addr first (not NULL)
        memcpy(&image_buffer_addr[buffer_index], &buffer[1], data_length);

        buffer_index += data_length;

        printf("image_buffer (packet=%d, len=%d): ", packet_index, buffer_index);
        print_buf(&image_buffer_addr[0], buffer_index);

        packet_index++;
        break;

    default:
        break;
    }

    // print_buf(buffer, bufsize);
    // tud_hid_report(0, &num, 1);

}
