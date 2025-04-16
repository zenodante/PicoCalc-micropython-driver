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
#include "font6x8e500.h"


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
#define CORE1_STACK_SIZE 1024
uint32_t core1_stack[CORE1_STACK_SIZE];

static uint st_dma;
static uint8_t *frameBuff;

static volatile bool autoUpdate;
static uint16_t lineBuffA[64];
static uint16_t lineBuffB[64];
void (*pColorUpdate)(uint8_t *, uint32_t, const uint16_t *);
void (*pSetPixel)(int32_t,int32_t,uint16_t);
static uint8_t currentTextY;
static uint8_t currentTextX;
static const uint8_t *currentTextTable;
static uint16_t LUT[256] = {
    //0x0000, 0x4A19, 0x2A79, 0x2A04, 0x86AA, 0xA95A, 0x18C6, 0x9DFF, 
    //0x09F8, 0x00FD, 0x64FF, 0x2607, 0x7F2D, 0xB383, 0xB5FB, 0x75FE
    0x0000, 0x0080, 0x0004, 0x0084, 0x1000, 0x1080, 0x1004, 0x18C6,
    0x1084, 0x00F8, 0xE007, 0xE0FF, 0x1F00, 0x1FF8, 0xFF07, 0xFFFF,
    0x0000, 0x0B00, 0x1000, 0x1500, 0x1A00, 0x1F00, 0xE002, 0xEB02,
    0xF002, 0xF502, 0xFA02, 0xFF02, 0x2004, 0x2B04, 0x3004, 0x3504,
    0x3A04, 0x3F04, 0x6005, 0x6B05, 0x7005, 0x7505, 0x7A05, 0x7F05,
    0xA006, 0xAB06, 0xB006, 0xB506, 0xBA06, 0xBF06, 0xE007, 0xEB07,
    0xF007, 0xF507, 0xFA07, 0xFF07, 0x0058, 0x0B58, 0x1058, 0x1558,
    0x1A58, 0x1F58, 0xE05A, 0xEB5A, 0xF05A, 0xF55A, 0xFA5A, 0xFF5A,
    0x205C, 0x2B5C, 0x305C, 0x355C, 0x3A5C, 0x3F5C, 0x605D, 0x6B5D,
    0x705D, 0x755D, 0x7A5D, 0x7F5D, 0xA05E, 0xAB5E, 0xB05E, 0xB55E,
    0xBA5E, 0xBF5E, 0xE05F, 0xEB5F, 0xF05F, 0xF55F, 0xFA5F, 0xFF5F,
    0x0080, 0x0B80, 0x1080, 0x1580, 0x1A80, 0x1F80, 0xE082, 0xEB82,
    0xF082, 0xF582, 0xFA82, 0xFF82, 0x2084, 0x2B84, 0x3084, 0x3584,
    0x3A84, 0x3F84, 0x6085, 0x6B85, 0x7085, 0x7585, 0x7A85, 0x7F85,
    0xA086, 0xAB86, 0xB086, 0xB586, 0xBA86, 0xBF86, 0xE087, 0xEB87,
    0xF087, 0xF587, 0xFA87, 0xFF87, 0x00A8, 0x0BA8, 0x10A8, 0x15A8,
    0x1AA8, 0x1FA8, 0xE0AA, 0xEBAA, 0xF0AA, 0xF5AA, 0xFAAA, 0xFFAA,
    0x20AC, 0x2BAC, 0x30AC, 0x35AC, 0x3AAC, 0x3FAC, 0x60AD, 0x6BAD,
    0x70AD, 0x75AD, 0x7AAD, 0x7FAD, 0xA0AE, 0xABAE, 0xB0AE, 0xB5AE,
    0xBAAE, 0xBFAE, 0xE0AF, 0xEBAF, 0xF0AF, 0xF5AF, 0xFAAF, 0xFFAF,
    0x00D0, 0x0BD0, 0x10D0, 0x15D0, 0x1AD0, 0x1FD0, 0xE0D2, 0xEBD2,
    0xF0D2, 0xF5D2, 0xFAD2, 0xFFD2, 0x20D4, 0x2BD4, 0x30D4, 0x35D4,
    0x3AD4, 0x3FD4, 0x60D5, 0x6BD5, 0x70D5, 0x75D5, 0x7AD5, 0x7FD5,
    0xA0D6, 0xABD6, 0xB0D6, 0xB5D6, 0xBAD6, 0xBFD6, 0xE0D7, 0xEBD7,
    0xF0D7, 0xF5D7, 0xFAD7, 0xFFD7, 0x00F8, 0x0BF8, 0x10F8, 0x15F8,
    0x1AF8, 0x1FF8, 0xE0FA, 0xEBFA, 0xF0FA, 0xF5FA, 0xFAFA, 0xFFFA,
    0x20FC, 0x2BFC, 0x30FC, 0x35FC, 0x3AFC, 0x3FFC, 0x60FD, 0x6BFD,
    0x70FD, 0x75FD, 0x7AFD, 0x7FFD, 0xA0FE, 0xABFE, 0xB0FE, 0xB5FE,
    0xBAFE, 0xBFFE, 0xE0FF, 0xEBFF, 0xF0FF, 0xF5FF, 0xFAFF, 0xFFFF,
    0x4108, 0x8210, 0xE318, 0x2421, 0x8631, 0xC739, 0x2842, 0x694A,
    0xCB5A, 0x0C63, 0x6D6B, 0xAE73, 0x1084, 0x518C, 0xB294, 0xF39C,
    0x55AD, 0x96B5, 0xF7BD, 0x38C6, 0x9AD6, 0xDBDE, 0x3CE7, 0x7DEF,
};//standar vt100 color table with byte sweep


static void Write_dma(const uint8_t *src, size_t len);
static void command(uint8_t com, size_t len, const char *data) ;
void RGB565Update(uint8_t *frameBuff,uint32_t length, const uint16_t *LUT);
void LUT8Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
void LUT4Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
void LUT2Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
void LUT1Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT);
//void core1_main(void);
void setpixelRGB565(int32_t x, int32_t y,uint16_t color);
void setpixelLUT8(int32_t x, int32_t y,uint16_t color);
void setpixelLUT4(int32_t x, int32_t y,uint16_t color);
void setpixelLUT2(int32_t x, int32_t y,uint16_t color);
void setpixelLUT1(int32_t x, int32_t y,uint16_t color);

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
  //multicore_lockout_victim_init();
  static int frame = 0;
  while (1) {
    if (++frame % 100 == 0) {
      printf("Core1 alive: %d\n", frame);
    }
    if (autoUpdate){
      pColorUpdate(frameBuff,DISPLAY_HEIGHT*DISPLAY_WIDTH, LUT);
    }     
    sleep_ms(5); 

  }
}


void setpixelRGB565(int32_t x, int32_t y,uint16_t color){
  ((uint16_t *)frameBuff)[x + DISPLAY_WIDTH*y]= color;
}

void setpixelLUT8(int32_t x, int32_t y,uint16_t color){
  ((uint8_t *)frameBuff)[x + DISPLAY_WIDTH*y]= (uint8_t)color;
}

void setpixelLUT4(int32_t x, int32_t y,uint16_t color){
  uint8_t *pixel = &((uint8_t *)frameBuff)[(x + (DISPLAY_WIDTH*y))>>1];

  if (x&0x01) {
    *pixel = ((uint8_t)color & 0x0f) | (*pixel & 0xf0);
  } else {
    *pixel = ((uint8_t)color << 4) | (*pixel & 0x0f);
  }
}

void setpixelLUT2(int32_t x, int32_t y,uint16_t color){
  uint8_t *pixel = &((uint8_t *)frameBuff)[(x + (DISPLAY_WIDTH*y))>>2];
  uint8_t shift = (x & 0x3) << 1;
  uint8_t mask = 0x3 << shift;
  color = ((uint8_t)color & 0x3) << shift;
  *pixel = color | (*pixel & (~mask));
}

void setpixelLUT1(int32_t x, int32_t y,uint16_t color){
  size_t index = (x + y * DISPLAY_WIDTH) >> 3;
  unsigned int offset =  x & 0x07;
  ((uint8_t *)frameBuff)[index] = (((uint8_t *)frameBuff)[index] & ~(0x01 << offset)) | ((color != 0) << offset);
}

static mp_obj_t pd_init(mp_obj_t fb_obj, mp_obj_t color_type, mp_obj_t autoR){
    mp_buffer_info_t buf_info;
    mp_get_buffer_raise(fb_obj, &buf_info, MP_BUFFER_READ);
    frameBuff=(uint8_t *)buf_info.buf;
    autoUpdate = mp_obj_is_true(autoR);

    int32_t colorType = mp_obj_get_int(color_type);
    currentTextY = 8;
    currentTextX = 6;
    currentTextTable=font6x8tt;
    switch (colorType){
      case 1: //565
        pColorUpdate = RGB565Update;
        pSetPixel = setpixelRGB565;
        break;
      case 2: //16 color
        pColorUpdate = LUT4Update;
        pSetPixel = setpixelLUT4;
        break;
      case 4: //2 color
        pColorUpdate = LUT1Update;
        pSetPixel = setpixelLUT1;
        break;
      case 5: //4 color
        pColorUpdate = LUT2Update;
        pSetPixel = setpixelLUT2;
        break;
      case 6: //256 color
        pColorUpdate = LUT8Update;
        pSetPixel = setpixelLUT8;
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

    //sleep_ms(100);
    //pColorUpdate(frameBuff,DISPLAY_HEIGHT*DISPLAY_WIDTH, LUT);
    //sleep_ms(10);
    if autoUpdate==true){
      multicore_reset_core1();
      multicore_launch_core1_with_stack(core1_main, core1_stack, CORE1_STACK_SIZE);
    }
    //multicore_launch_core1_with_stack(core1_main, core1_stack, CORE1_STACK_SIZE);

    return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_3(pd_init_obj, pd_init);


static mp_obj_t drawTxt6x8(mp_uint_t n_args, const mp_obj_t *args){
  // extract arguments

  const char *str = mp_obj_str_get_str(args[0]);
  int x0 = mp_obj_get_int(args[1]);
  int y0 = mp_obj_get_int(args[2]);
  uint16_t color = mp_obj_get_int(args[3]);
  int x;
  int y;

  // loop over chars
  for (; *str; ++str) {
      // get char and make sure its in range of font
    int chr = *(uint8_t *)str;
    if (chr < 32 ) {
      chr = 32;
    }
      // get char data
    const uint8_t *chr_data = &currentTextTable[(chr - 32) * currentTextY];
      // loop over char data
    y = y0;
      
    for (; y < y0+currentTextY; y++) {
      
      if (0 <= y && y < DISPLAY_HEIGHT) {
        x = x0;
        uint8_t line_data = *chr_data++; 
        for (;x<x0+currentTextX-1;x++){

          if ((line_data&0x80)&&(0 <= x && x < DISPLAY_WIDTH)) { // only draw if pixel set
              pSetPixel(x, y, color);
            }
          line_data <<= 1;
        }
      }    
    }
    x0 +=currentTextX;
  }
  return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(drawTxt6x8_obj, 4, 4, drawTxt6x8);



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
  multicore_reset_core1();
  multicore_launch_core1_with_stack(core1_main, core1_stack, CORE1_STACK_SIZE);
  return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_0(startAutoUpdate_obj, startAutoUpdate);


static mp_obj_t stopAutoUpdate(void){
  autoUpdate = false;
  multicore_reset_core1();
  return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_0(stopAutoUpdate_obj, stopAutoUpdate);


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




static mp_obj_t pd_update(){
    if (autoUpdate==false){
      pColorUpdate(frameBuff,DISPLAY_HEIGHT*DISPLAY_WIDTH, LUT);
    }
    return mp_const_true;
}
static MP_DEFINE_CONST_FUN_OBJ_0(pd_update_obj, pd_update);


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
    while (spi_get_hw(SPI_DISP)->sr & SPI_SSPSR_BSY_BITS) {
      tight_loop_contents();  
    }
    gpio_put(CS_PIN, 1);    
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
    while (spi_get_hw(SPI_DISP)->sr & SPI_SSPSR_BSY_BITS) {
      tight_loop_contents(); 
    }
    gpio_put(CS_PIN, 1);
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
    while (spi_get_hw(SPI_DISP)->sr & SPI_SSPSR_BSY_BITS) {
      tight_loop_contents(); 
    }
    gpio_put(CS_PIN, 1);
  }
  
  void LUT2Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT){
    while (dma_channel_is_busy(st_dma));
    //uint16_t lineBuffA[64];
    //uint16_t lineBuffB[64];
    uint16_t *currentLineBuff=lineBuffA;
    uint16_t *updateLineBuff=lineBuffA;
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
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
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
        currentPixel = *frameBuff++;color = LUT[currentPixel&0x03];*currentLineBuff++ = color;
        color = LUT[(currentPixel>>2)&0x03];*currentLineBuff++ = color;
        color = LUT[(currentPixel>>4)&0x03];*currentLineBuff++ = color;
        color = LUT[(currentPixel>>6)];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)lineBuffB,leftPixels*8);
    }
    while (dma_channel_is_busy(st_dma));
    while (spi_get_hw(SPI_DISP)->sr & SPI_SSPSR_BSY_BITS) {
      tight_loop_contents(); 
    }
    gpio_put(CS_PIN, 1);
}  
  
void LUT1Update(uint8_t *frameBuff, uint32_t length,  const uint16_t *LUT){
    while (dma_channel_is_busy(st_dma));
    //uint16_t lineBuffA[64];
    //uint16_t lineBuffB[64];
    uint16_t *currentLineBuff=lineBuffA;
    uint16_t *updateLineBuff=lineBuffA;
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
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
          currentPixel = *frameBuff++;color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
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
        currentPixel = *frameBuff++;color = LUT[currentPixel&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x01)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x02)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x03)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x04)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x05)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x06)&0x01];*currentLineBuff++ = color;
          color = LUT[(currentPixel>>0x07)&0x01];*currentLineBuff++ = color;
      }
      while (dma_channel_is_busy(st_dma));
      Write_dma((const uint8_t *)lineBuffB,leftPixels*16);
    }
    while (dma_channel_is_busy(st_dma));
    while (spi_get_hw(SPI_DISP)->sr & SPI_SSPSR_BSY_BITS) {
      tight_loop_contents(); 
    }
    gpio_put(CS_PIN, 1);
  }
  
  




// Define all attributes of the module.
// Table entries are key/value pairs of the attribute name (a string)
// and the MicroPython object reference.
// All identifiers and strings are written as MP_QSTR_xxx and will be
// optimized to word-sized integers by the build system (interned strings).
static const mp_rom_map_elem_t picocalcdisplay_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalcdisplay) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&pd_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_setLUT), MP_ROM_PTR(&setLUT_obj) },
    { MP_ROM_QSTR(MP_QSTR_update), MP_ROM_PTR(&pd_update_obj) },
    { MP_ROM_QSTR(MP_QSTR_startAutoUpdate), MP_ROM_PTR(&startAutoUpdate_obj) },
    { MP_ROM_QSTR(MP_QSTR_stopAutoUpdate), MP_ROM_PTR(&stopAutoUpdate_obj) },
    { MP_ROM_QSTR(MP_QSTR_drawTxt6x8), MP_ROM_PTR(&drawTxt6x8_obj) },
};
static MP_DEFINE_CONST_DICT(picocalcdisplay_globals, picocalcdisplay_globals_table);

// Define module object.
const mp_obj_module_t picocalcdisplay_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalcdisplay_globals,
};

// Register the module to make it available in Python.
MP_REGISTER_MODULE(MP_QSTR_picocalcdisplay, picocalcdisplay_module);
