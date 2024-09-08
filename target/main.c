#include <stdio.h>
#include <string.h>
#include "epd/epd/platforms/platform.h"

#include "tusb.h"
#include "tinyusb/tud_callbacks.h"
#include "epd/epd/panels/E2B98FS081.h"
#include "hardware/watchdog.h"
#include "image_data.h"
#include "include/tasks.h"
#include "pico/multicore.h"
#include "pico/util/queue.h"
#include "tusb.h"

uint8_t image_buffer[2*IMAGE_SIZE_BYTES] = {0};
queue_t core1_control_queue;

void core1_main(void);

// TODO: there's no reason to use the HAL except for init & panel API
int main() {
    console.init();
    time.sleep_ms(2500);

    gpio.init(PIN_LED);
    gpio.mode(PIN_LED, OUTPUT);

    tusb_init();

    queue_init(&core1_control_queue, sizeof(uint8_t), 1);
    multicore_launch_core1(core1_main);

    if (watchdog_enable_caused_reboot()) {
        printf("watchdog timeout reboot!\n");
    }

    watchdog_enable(500, 1);

    console.debug("init done\n");

    while (1) {
        tud_task();
        management_task();
        led_blink_task();
        watchdog_update();
    }
}

void core1_main(void) {
    // Load a pre-formatted image from image_data.h
    memcpy(image_buffer, image_data, 2*IMAGE_SIZE_BYTES);

    while(true) {
        uint8_t entry;
        queue_remove_blocking(&core1_control_queue, &entry);

        panel.init();
        panel.write(image_buffer, 2*IMAGE_SIZE_BYTES);
        panel.refresh();
        panel.shutdown();
    }
}
