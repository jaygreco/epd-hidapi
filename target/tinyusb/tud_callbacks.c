#include "class/cdc/cdc_device.h"
#include "epd/epd/panels/E2B98FS081.h"
#include "include/csum.h"
#include "pico/multicore.h"
#include "pico/util/queue.h"
#include "tinyusb/tud_callbacks.h"
#include "tusb.h"

extern uint8_t image_buffer[];
extern queue_t core1_control_queue;

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

    // TODO: check length, incl. max length + commands
    // TODO: bounds checks
    switch (buffer[0]) {
    case CMD_BUF_RESET: {
        printf("CMD_BUF_RESET\n");
        buffer_index = 0;
        packet_index = 0;
        memset(image_buffer, 0, 2*IMAGE_SIZE_BYTES);
        break;
    }

    case CMD_BUF_SET_ADDR: {
        if (bufsize < 4) {
            printf("CMD_BUF_SET_ADDR: missing parameters\n");
            break;
        }

        buffer_index = (buffer[1] | (buffer[2] << 8) | buffer[3] << 16);

        if (buffer_index > 2*IMAGE_SIZE_BYTES) {
            printf("CMD_BUF_SET_ADDR: buffer_index (0x%x) > 2*IMAGE_SIZE_BYTES (%d)\n", buffer_index, 2*IMAGE_SIZE_BYTES);
            break;
        }

        printf("CMD_BUF_SET_ADDR: 0x%x (%d)\n", buffer_index, buffer_index);
        packet_index = 0;
        break;
    }

    case CMD_BUF_SET_DATA: {

        if (bufsize < 2) {
            printf("CMD_BUF_SET_DATA: missing parameters\n");
            break;
        }
        if (!image_buffer) {
            printf("CMD_BUF_SET_DATA: missing image_buffer\n");
            break;
        }

        uint32_t data_length = bufsize - 1;

        if (buffer_index > 2*IMAGE_SIZE_BYTES || buffer_index + data_length > 2*IMAGE_SIZE_BYTES) {
            printf("CMD_BUF_SET_DATA: buffer_index/data_length (0x%x/0x%0x) > 2*IMAGE_SIZE_BYTES (%d)\n", buffer_index, data_length, 2*IMAGE_SIZE_BYTES);
            break;
        }

        printf("CMD_BUF_SET_DATA (packet=%d, len=%d)\n", packet_index, data_length);
        // print_buf(buffer, bufsize);
        memcpy(&image_buffer[buffer_index], &buffer[1], data_length);
        buffer_index += data_length;
        // printf("image_buffer (packet=%d, len=%d): ", packet_index, buffer_index);
        // print_buf(image_buffer, buffer_index);
        packet_index++;
        break;
    }


    // Run checksum up to <data_length> starting at <buffer_index>
    case CMD_BUF_CHECKSUM: {
        if (bufsize < 4) {
            printf("CMD_BUF_CHECKSUM: missing parameters\n");
            break;
        }
        if (!image_buffer) {
            printf("CMD_BUF_CHECKSUM: missing image_buffer\n");
            break;
        }

        uint32_t data_length = (buffer[1] | (buffer[2] << 8) | buffer[3] << 16);

        if (!data_length > 2*IMAGE_SIZE_BYTES) {
            printf("CMD_BUF_CHECKSUM: data_length (%d bytes) > 2*IMAGE_SIZE_BYTES (%d)\n", data_length, 2*IMAGE_SIZE_BYTES);
            break;
        }

        uint32_t checksum = csum(&image_buffer[buffer_index], data_length);
        uint8_t result[4] = {checksum & 0xFF, checksum >> 8 & 0xFF, checksum >> 16 & 0xFF, checksum >> 24 & 0xFF};
        tud_hid_report(0, &result, 4);
        printf("CMD_BUF_CHECKSUM: 0x%08x (start 0x%x, len %d)\n", checksum, buffer_index, data_length);
        break;
    }
    
    case CMD_PANEL_REFRESH: {
        printf("CMD_PANEL_REFRESH\n");
        // Use the core1 control queue to resume execution on core1
        // If there is already an entry in the queue, don't add another
        uint8_t value = 0;
        queue_try_add(&core1_control_queue, &value);
        break;
    }

    default:
        printf("command (0x%02x) not implemented\n", buffer[0]);
        break;
    }
    // tud_hid_report(0, buffer, bufsize);

    // printf("hid callback (bufsize=%d)\n", bufsize);
    // print_buf(buffer, bufsize);

}
