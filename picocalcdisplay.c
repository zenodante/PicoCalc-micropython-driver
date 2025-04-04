#include "picocalcdisplay.h"
// Include MicroPython API.
#include "py/runtime.h"

// Used to get the time in the Timer class example.
#include "py/mphal.h"
#include "py/gc.h"
#include "py/misc.h"
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "hardware/spi.h"
#include "hardware/dma.h"
#include "hardware/gpio.h"
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/sync.h"

#define    SWRESET   0x01
#define    SLPOUT    0x11
#define    INVON     0x21
#define    DISPON    0x29
#define    CASET     0x2A
#define    RASET     0x2B
#define    RAMWR     0x2C
#define    TEON      0x35
#define    MADCTL    0x36  // Memory Data Access Control
#define    COLMOD    0x3A//
#define    FRMCTR1   0xB1
#define    INVCTR    0xB4
#define    ETMOD     0xB7
#define    CECTRL1   0xB9
#define    PWCTR1    0xC0
#define    PWCTR2    0xC1
#define    PWCTR3    0xC2
#define    VMCTR1    0xC5
#define    PGAMCTRL  0xE0
#define    NGAMCTRL  0xE1

static uint st_dma;
static uint8_t *frameBuff;
static uint8_t colorType;
static volatile bool autoUpdate;
static uint16_t lineBuffA[64];
static uint16_t lineBuffB[64];
void (*pColorUpdate)(uint8_t *, uint32_t, const uint16_t *);

static uint16_t LUT[256] = {//vt100 type 16 colors
    //0x0000, 0x4A19, 0x2A79, 0x2A04, 0x86AA, 0xA95A, 0x18C6, 0x9DFF, 
    //0x09F8, 0x00FD, 0x64FF, 0x2607, 0x7F2D, 0xB383, 0xB5FB, 0x75FE
    0x0000,0x00A0,0xA004,0xA0A6,0x1D00,0x15A0,0xBD04,0x7DEF,
    0x1084,0x00F8,0xE007,0xE0FF,0x9F52,0x1FF8,0xFF07,0xFFFF
};


static void Write_dma(const uint8_t *src, size_t len);
static void command(uint8_t com, size_t len, const char *data) ;
void RGB565Update(uint8_t *frameBuff,uint32_t length,const uint16_t *LUT);
void LUT8Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
void LUT4Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
void LUT2Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
void LUT1Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
void core1_main(void);
/*
#define FRAMEBUF_MVLSB    (0)
#define FRAMEBUF_RGB565   (1)
#define FRAMEBUF_GS2_HMSB (5)
#define FRAMEBUF_GS4_HMSB (2)
#define FRAMEBUF_GS8      (6)
#define FRAMEBUF_MHLSB    (3)
#define FRAMEBUF_MHMSB    (4)
*/


void core1_main() {
  while (true) {
      if (autoUpdate) {
          __dmb();
          pColorUpdate(frameBuff,DISPLAY_HEIGHT*DISPLAY_WIDTH, LUT);
          sleep_ms(1); 
      } else {
          __wfe();
      }
  }
}

static mp_obj_t init(mp_obj_t fb_obj, mp_obj_t colorType, mp_obj_t auto){
    mp_buffer_info_t buf_info;
    mp_get_buffer_raise(fb_obj, &buf_info, MP_BUFFER_READ);
    frameBuff=(uint8_t *)buf_info.buf;
    bool autoUpdate = mp_obj_is_true(auto);

    colorType = mp_obj_get_uint(colorType);

    switch (colorType){
      case 1: //565
        pColorUpdate = RGB565Update;
        break;
      case 2: //16 color
        pColorUpdate = LUT4Update;
        break;
      case 4: //2 color
        pColorUpdate = LUT1Update;
        break;
      case 5: //4 color
        pColorUpdate = LUT2Update;
        break;
      case 6: //256 color
        pColorUpdate = LUT8Update;
        break;
 
    }
 //spi init
    spi_init(SPI_DISP, 25000000);
    gpio_set_function(CLK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(MOSI_PIN, GPIO_FUNC_SPI);

    gpio_init(CS_PIN);
    gpio_put(CS_PIN, 1);
    gpio_set_dir(CS_PIN, GPIO_OUT);

    gpio_init(DC_PIN);
    gpio_set_dir(DC_PIN, GPIO_OUT);

    gpio_init(RST_PIN);
    gpio_put(RST_PIN, 0);
    gpio_set_dir(RST_PIN, GPIO_OUT);
//DMA init
    st_dma = dma_claim_unused_channel(true);
    dma_channel_config config = dma_channel_get_default_config(st_dma);
    channel_config_set_transfer_data_size(&config, DMA_SIZE_8);
    channel_config_set_bswap(&config, false);
    channel_config_set_dreq(&config, spi_get_dreq(SPI_DISP, true));
    dma_channel_configure(st_dma, &config, &spi_get_hw(SPI_DISP)->dr, NULL, 0, false);
    gpio_put(RST_PIN, 0);
    sleep_ms(100);
    gpio_put(RST_PIN, 1);
    sleep_ms(150);
    command(SWRESET,0,NULL);
    sleep_ms(150);
    command(SLPOUT,0,NULL);
    sleep_ms(500);
    command(0xF0,1,"\xC3");
    command(0xF0,1,"\x96");
    command(MADCTL,1,"\x48");
    command(COLMOD,1,"\x65");//pixel format rgb565
    command(FRMCTR1,1,"\xA0");
    command(INVCTR,1,"\x00");
    command(ETMOD,1,"\xC6");
    command(CECTRL1,2,"\x02\xE0");
    command(PWCTR1,2,"\x80\x06");
    command(PWCTR2,1,"\x15");
    command(PWCTR3,1,"\xA7");
    command(VMCTR1,1,"\x04");
    command(0xE8,8,"\x40\x8A\x00\x00\x29\x19\xAA\x33");
    command(PGAMCTRL,14,"\xF0\x06\x0F\x05\x04\x20\x37\x33\x4C\x37\x13\x14\x2B\x31");
    command(NGAMCTRL,14,"\xF0\x11\x1B\x11\x0F\x0A\x37\x43\x4C\x37\x13\x13\x2C\x32");

    command(0xF0,1,"\x3C");
    command(0xF0,1,"\x69");
    command(TEON,1,"\x00");
    command(SLPOUT,0,NULL);
    sleep_ms(120);
    command(DISPON,0,NULL);
    sleep_ms(120);
    command(INVON,0,NULL);
    command(CASET,4,"\x00\x00\x01\x3F");
    command(RASET,4,"\x00\x00\x01\x3F");

    command(RAMWR,0,NULL);


    multicore_launch_core1(core1_main);

    return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_3(init_obj, init);


static mp_obj_t setLUT(mp_obj_t LUT_obj){
    mp_buffer_info_t buf_info;
    mp_get_buffer_raise(LUT_obj, &buf_info, MP_BUFFER_READ);
    size_t bufLen = buf_info.len;
    
    memcpy(LUT,buf_info.buf,bufLen* sizeof(uint16_t));
    
    return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_1(setLUT_obj, setLUT);

static mp_obj_t startAutoUpdate(void){
  autoUpdate = true;
  __sev();
  return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_1(startAutoUpdate_obj, startAutoUpdate);


static mp_obj_t stopAutoUpdate(void){
  autoUpdate = false;
  return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_1(stopAutoUpdate_obj, stopAutoUpdate);


static void Write_dma(const uint8_t *src, size_t len) {
    while (dma_channel_is_busy(st_dma));
    dma_channel_set_trans_count(st_dma, len, false);
    dma_channel_set_read_addr(st_dma, src, true);
}


static void command(uint8_t com, size_t len, const char *data) {
    
    gpio_put(CS_PIN, 0);
    gpio_put(DC_PIN, 0); // command mode
    spi_write_blocking(SPI_DISP,&com, 1);    
    if(data) {
      gpio_put(DC_PIN, 1); // data mode
      spi_write_blocking(SPI_DISP,(const uint8_t*)data, len);    
    }
    gpio_put(CS_PIN, 1);
}




static mp_obj_t update(){
    if (autoUpdate==false){
      pColorUpdate(frameBuff,DISPLAY_HEIGHT*DISPLAY_WIDTH, LUT);
    }
    return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_0(update_obj, update);


void RGB565Update(uint8_t *frameBuff,uint32_t length,const uint16_t *LUT) {
    //gpio_put(CS_PIN, 1);
    //gpio_put(CS_PIN, 0);
    while (dma_channel_is_busy(st_dma));
    uint8_t cmd = RAMWR;
    gpio_put(CS_PIN, 0);
    gpio_put(DC_PIN, 0); // command mode
    
    spi_write_blocking(SPI_DISP,&cmd, 1);

    gpio_put(DC_PIN, 1); // data mode
    Write_dma((const uint8_t*)frameBuff, length*2);    
    while (dma_channel_is_busy(st_dma));
    gpio_put(CS, 1);    
}

void LUT8Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT){
    while (dma_channel_is_busy(st_dma));
    //uint16_t lineBuffA[64];
    //uint16_t lineBuffB[64];
    uint16_t *currentLineBuff=lineBuffA;
    uint16_t *updateLineBuff=lineBuffA;
    uint32_t leftPixels = length - (length&0xFFFFFFC0);
    uint32_t count = length>>6;
    uint8_t currentPixel=0;
    uint16_t color;
    uint8_t cmd = RAMWR;
    gpio_put(CS_PIN, 0);
    gpio_put(DC_PIN, 0); // command mode
    
    spi_write_blocking(SPI_DISP,&cmd, 1);
    gpio_put(DC_PIN, 1); // data mode
    while(count--){
      if (count&0x00000001){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      for (int i=2;i>0;i--){
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)updateLineBuff,64*2);
    }
    if (leftPixels != 0){
      if   (updateLineBuff == lineBuffB){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      while(leftPixels--){
        currentPixel = *frameBuff++;color = LUT[currentPixel];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)lineBuffB,leftPixels*2);
    }
    while (dma_channel_is_busy(st_dma));
    gpio_put(CS, 1);
  }
  
  
  void LUT4Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT){
    while (dma_channel_is_busy(st_dma));
    //uint16_t lineBuffA[64];
    //uint16_t lineBuffB[64];
    uint16_t *currentLineBuff =lineBuffA;
    uint16_t *updateLineBuff =lineBuffA;
    uint32_t leftPixels = (length - (length&0xFFFFFFC0))>>1;
    uint32_t count = length>>6;
    uint8_t currentPixel=0;
    uint16_t color;
    uint8_t cmd = RAMWR;
    gpio_put(CS_PIN, 0);
    gpio_put(DC_PIN, 0); // command mode
    
    spi_write_blocking(SPI_DISP,&cmd, 1);
    gpio_put(DC_PIN, 1); // data mode
    while(count--){
      if (count&0x00000001){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      for (int i=2;i>0;i--){
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)updateLineBuff,64*2);
    }
    if (leftPixels != 0){
      if   (updateLineBuff == lineBuffB){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      
      while(leftPixels--){
        currentPixel = *frameBuff++;color = LUT[currentPixel>>4];*currentLineBuff++ = color;
        color = LUT[currentPixel&0x0F];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)lineBuffB,leftPixels*4);
    }
    while (dma_channel_is_busy(st_dma));
    gpio_put(CS, 1);
  }
  
  void LUT2Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT){
    while (dma_channel_is_busy(st_dma));
    //uint16_t lineBuffA[64];
    //uint16_t lineBuffB[64];
    uint16_t *currentLineBuff;
    uint16_t *updateLineBuff;
    uint32_t leftPixels = (length - (length&0xFFFFFFC0))>>2;
    uint32_t count = length>>6;
    uint8_t currentPixel=0;
    uint16_t color;
    uint8_t cmd = RAMWR;
    gpio_put(CS_PIN, 0);
    gpio_put(DC_PIN, 0); // command mode
    
    spi_write_blocking(SPI_DISP,&cmd, 1);
    gpio_put(DC_PIN, 1); // data mode
    while(count--){
      if (count&0x00000001){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      for (int i=2;i>0;i--){
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)updateLineBuff,64*2);
    }
    if (leftPixels != 0){
      if   (updateLineBuff == lineBuffB){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      
      while(leftPixels--){
        currentPixel = *frameBuff++;color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
        color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
        color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
        color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)lineBuffB,leftPixels*8);
    }
    while (dma_channel_is_busy(st_dma));
    gpio_put(CS, 1);
}  
  
void LUT1Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT){
    while (dma_channel_is_busy(st_dma));
    //uint16_t lineBuffA[64];
    //uint16_t lineBuffB[64];
    uint16_t *currentLineBuff;
    uint16_t *updateLineBuff;
    uint32_t leftPixels = (length - (length&0xFFFFFFC0))>>3;
    uint32_t count = length>>6;
    uint8_t currentPixel=0;
    uint16_t color;
    uint8_t cmd = RAMWR;
    gpio_put(CS_PIN, 0);
    gpio_put(DC_PIN, 0); // command mode
    
    spi_write_blocking(SPI_DISP,&cmd, 1);
    gpio_put(DC_PIN, 1); // data mode
    while(count--){
      if (count&0x00000001){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      for (int i=2;i>0;i--){
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)updateLineBuff,64*2);
    }
    if (leftPixels != 0){
      if   (updateLineBuff == lineBuffB){
        currentLineBuff = lineBuffA;
        updateLineBuff = lineBuffA;
      }else{
        currentLineBuff = lineBuffB;
        updateLineBuff = lineBuffB;
      }
      
      while(leftPixels--){
        currentPixel = *frameBuff++;color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)lineBuffB,leftPixels*16);
    }
    while (dma_channel_is_busy(st_dma));
    gpio_put(CS, 1);
  }
  
  




// Define all attributes of the module.
// Table entries are key/value pairs of the attribute name (a string)
// and the MicroPython object reference.
// All identifiers and strings are written as MP_QSTR_xxx and will be
// optimized to word-sized integers by the build system (interned strings).
static const mp_rom_map_elem_t picocalcdisplay_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalcdisplay) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&init_obj) },
    { MP_ROM_QSTR(MP_QSTR_setLUT), MP_ROM_PTR(&setLUT_obj) },
    { MP_ROM_QSTR(MP_QSTR_update), MP_ROM_PTR(&update_obj) },
    { MP_ROM_QSTR(MP_QSTR_startAutoUpdate), MP_ROM_PTR(&startAutoUpdate_obj) },
    { MP_ROM_QSTR(MP_QSTR_stopAutoUpdate), MP_ROM_PTR(&stopAutoUpdate_obj) },

};
static MP_DEFINE_CONST_DICT(picocalcdisplay_globals, picocalcdisplay_globals_table);

// Define module object.
const mp_obj_module_t picocalcdisplay_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalcdisplay_globals,
};

// Register the module to make it available in Python.
MP_REGISTER_MODULE(MP_QSTR_picocalcdisplay, picocalcdisplay_module);
