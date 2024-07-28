#include <stdio.h>
#include <string.h>
#include "epd/epd/platforms/platform.h"
#include "epd/epd/panels/E2B98FS081.h"
#include "image_data.h"
#include "pico/multicore.h"
#include "include/tasks.h"

void core1_main(void);

int main() {
    console.init();
    time.sleep_ms(2500);

    gpio.init(PIN_LED);
    gpio.mode(PIN_LED, OUTPUT);

    multicore_launch_core1(core1_main);

    while (1) {
        led_blink_task();
        management_task();
    }
}

// Note that because of the stack layout, large stack allocations need to
// happen on core1. If core0 makes an allocation larget than 4k, it will
// overrun into core1's stack and core1 will halt.
void core1_main(void) {
    uint8_t image_buffer[2*IMAGE_SIZE_BYTES] = {0};
    memcpy(image_buffer, image_data, 2*IMAGE_SIZE_BYTES);

    panel.init();
    panel.write(image_buffer, 2*IMAGE_SIZE_BYTES);
    panel.refresh();
    panel.shutdown();

    for(;;);
}
