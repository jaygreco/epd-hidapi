#include "class/cdc/cdc_device.h"
#include "epd/epd/panels/E2B98FS081.h"
#include "include/csum.h"
#include "pico/multicore.h"
#include "pico/util/queue.h"
#include "tinyusb/tud_callbacks.h"
#include "tusb.h"

extern uint8_t* image_buffer_addr;
extern queue_t core_control_queue;

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
    // TODO: use inline variable declarations 
    uint32_t data_length = 0;
    uint32_t checksum = 0;
    uint8_t blah = 123;

    // TODO: check length, incl. max length + commands
    // TODO: bounds checks
    switch (buffer[0]) {
    case CMD_BUF_RESET:
        printf("CMD_BUF_RESET\n");
        buffer_index = 0;
        packet_index = 0;
        memset(image_buffer_addr, 0, 2*IMAGE_SIZE_BYTES);
        break;

    case CMD_BUF_SET_ADDR:
        // LSB FIRST, 12 bits
        buffer_index = (buffer[1] | (buffer[2] << 8) | buffer[3] << 16); 
        printf("CMD_BUF_SET_ADDR: 0x%x (%d)\n", buffer_index, buffer_index);
        packet_index = 0;
        break;

    case CMD_BUF_SET_DATA:
        data_length = bufsize - 1;

        printf("CMD_BUF_SET_DATA (packet=%d, len=%d)\n", packet_index, data_length);

        // TODO: check buffer addr first (not NULL)
        memcpy(&image_buffer_addr[buffer_index], &buffer[1], data_length);

        buffer_index += data_length;

        printf("image_buffer (packet=%d, len=%d): ", packet_index, buffer_index);
        print_buf(image_buffer_addr, buffer_index);

        packet_index++;
        break;

    // Run checksum of <data_length> starting at <buffer_index>
    case CMD_BUF_CHECKSUM:
        // TODO: check entire array length for bounds
        data_length = (buffer[1] | (buffer[2] << 8) | buffer[3] << 16);
        checksum = csum(&image_buffer_addr[buffer_index], data_length);
        printf("CMD_BUF_CHECKSUM: 0x%08x (start 0x%08x, len %d)\n", checksum, buffer_index, data_length);
        tud_hid_report(0, &blah, 1);
        break;
    
    case CMD_PANEL_REFRESH:
        printf("CMD_PANEL_REFRESH\n");
        // Use the core control queue to resume execution on core1
        // If there is already an entry in the queue, don't add another
        queue_try_add(&core_control_queue, &blah);
        break;

    default:
        printf("command (0x%02x) not implemented");
        break;
    }

    // print_buf(buffer, bufsize);
    // tud_hid_report(0, &num, 1);

}
