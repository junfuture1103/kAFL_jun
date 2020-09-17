/*
 * This file is part of Redqueen.
 *
 * Sergej Schumilo, 2019 <sergej@schumilo.de>
 * Cornelius Aschermann, 2019 <cornelius.aschermann@rub.de>
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "tnt_cache.h"
#include <assert.h>
#include <sys/mman.h>
#include <string.h>

#include "pt/debug.h"

#define BIT(x)				(1ULL << (x))

static inline uint8_t asm_bsr(uint64_t x){
	asm ("bsrq %0, %0" : "=r" (x) : "0" (x));
	return x;
}

uint8_t process_tnt_cache(tnt_cache_t* self){
	uint8_t result;
	if (self->tnt){
		result = self->tnt_memory[self->pos];
		self->tnt--;
		self->pos = (self->pos + 1) % BUF_SIZE;

		/* debug */
		if (result == TAKEN) {
			debug_flow("result: TAKEN, self->tnt: %d", self->tnt);
		} else if (result == NOT_TAKEN) {
			debug_flow("result: NOT_TAKEN, self->tnt: %d", self->tnt);
		}

		return result;	// TAKEN or NOT_TAKEN
	}
	return TNT_EMPTY;
}

void append_tnt_cache(tnt_cache_t* self, uint8_t data){
	uint8_t bsr_ret;

	/* debug */
	debug_flow("append_tnt_cache(data=0x%02x) called.", data);
	bsr_ret = asm_bsr(data);
	debug_flow("bsf_ret: 0x%02x", bsr_ret);

	uint8_t bits = bsr_ret - SHORT_TNT_OFFSET;
	for(uint8_t i = SHORT_TNT_OFFSET; i < bits+SHORT_TNT_OFFSET; i++){
		self->tnt_memory[((self->max+bits-i)%BUF_SIZE)] = ((data) & BIT(i)) >> i;
	}

	self->tnt += bits;
	self->max = (self->max + bits) % BUF_SIZE;
}	

void append_tnt_cache_ltnt(tnt_cache_t* self, uint64_t data){
	uint8_t bits = asm_bsr(data)-LONG_TNT_MAX_BITS;
	for(uint8_t i = LONG_TNT_MAX_BITS; i < bits+LONG_TNT_MAX_BITS; i++){
		self->tnt_memory[((self->max+bits-i)%BUF_SIZE)] = ((data) & BIT(i)) >> i;
	}

	self->tnt += bits;
	self->max = (self->max + bits) % BUF_SIZE;
}	

bool is_empty_tnt_cache(tnt_cache_t* self){
	return (bool)!!(self->tnt);
}

int count_tnt(tnt_cache_t* self){
	return self->tnt;
}

tnt_cache_t* tnt_cache_init(void){
	tnt_cache_t* self = malloc(sizeof(tnt_cache_t));
	self->tnt_memory = (uint8_t*)mmap(NULL, BUF_SIZE, PROT_READ | PROT_WRITE, MAP_ANONYMOUS | MAP_PRIVATE, 0, 0);
	self->max = 0;
	self->pos = 0;
	self->tnt = 0;
	return self;
}

void tnt_cache_flush(tnt_cache_t* self){
	self->max = 0;
	self->pos = 0;
	self->tnt = 0;
}

void tnt_cache_destroy(tnt_cache_t* self){
	munmap(self->tnt_memory, BUF_SIZE);
	self->max = 0;
	self->pos = 0;
	self->tnt = 0;
}

