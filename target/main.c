#include <stdio.h>
#include <string.h>
#include "epd/epd/platforms/platform.h"

#include "tusb.h"
#include "tinyusb/tud_callbacks.h"
#include "epd/epd/panels/E2B98FS081.h"
#include "image_data.h"
#include "pico/multicore.h"
#include "include/tasks.h"
#include "tusb.h"

uint8_t* image_buffer_addr = 0;

void core1_main(void);

int main() {
    console.init();
    time.sleep_ms(2500);

    gpio.init(PIN_LED);
    gpio.mode(PIN_LED, OUTPUT);

    tusb_init();

    multicore_launch_core1(core1_main);

    console.debug("init done\n");

    while (1) {
        tud_task();
        management_task();
        led_blink_task();
    }
}

/*
Note that because of the stack layout, large stack allocations need to
happen on core1. If core0 makes an allocation larger than 4k, it will
overrun into core1's stack and core1 will halt. I'm too lazy to remap the
stack or change the stack size.
*/
void core1_main(void) {
    uint8_t image_buffer[2*IMAGE_SIZE_BYTES] = {0};
    image_buffer_addr = image_buffer;

    // memcpy(image_buffer, image_data, 2*IMAGE_SIZE_BYTES);

    // panel.init();
    // panel.write(image_buffer, 2*IMAGE_SIZE_BYTES);
    // panel.refresh();
    // panel.shutdown();

    for(;;);
}
