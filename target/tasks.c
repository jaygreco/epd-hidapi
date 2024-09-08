#include "include/tasks.h"
#include "epd/epd/platforms/platform.h"
#include "hardware/watchdog.h"
#include "pico/bootrom.h"

#define BLINK_INTERVAL_MS 100

static void enter_bootloader() {
    console.print("Rebooting into bootloader...\n");
    gpio.write(PIN_LED, HIGH);
    sleep_ms(10);
    reset_usb_boot(0, 1); // Enable only picoboot interface
    for (;;);
}

static void soft_reboot() {
    console.print("Rebooting...\n");
    gpio.write(PIN_LED, HIGH);
    sleep_ms(10);
    watchdog_reboot(0, 0, 0);
    for (;;);
}

void led_blink_task() {
    static uint8_t led_state = LOW;
    static uint32_t start_ms = 0;

    if (time.millis() - start_ms < BLINK_INTERVAL_MS)
        return;

    gpio.write(PIN_LED, led_state);

    start_ms += BLINK_INTERVAL_MS;
    led_state = ~led_state;
}

void management_task() {
    while (uart_is_readable_within_us(uart0, 100)) {
        uint8_t c = uart_getc(uart0);        

        switch (c) {
        case 'b':
            enter_bootloader();
            break;
        case 'r':
            soft_reboot();
            break;
        case 'h':
            for(;;);
        default:
            uart_putc_raw(uart0, c); 
            break;
        }
    }
}
