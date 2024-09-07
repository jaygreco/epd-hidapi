#pragma once

#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

#define STRIDE 4
#ifndef ARRAY_LEN
#define ARRAY_LEN(a) (sizeof(a) / sizeof(a[0]))
#endif
#ifndef MIN
#define MIN(a,b) (((a)<(b))?(a):(b))
#endif

static uint32_t _ss32(uint8_t bytes[], uint32_t len);
uint32_t csum(uint8_t bytes[], uint32_t len);

