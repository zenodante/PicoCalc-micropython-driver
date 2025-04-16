//A modified version of vt100 emulator from https://github.com/ht-deko/vt100_stm32

#include "vtterminal.h"
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include "py/runtime.h"

#include "py/mphal.h"
#include "py/gc.h"
#include "py/misc.h"
#include "font6x8e500_2.h"

#include "pico/stdlib.h"
#include "hardware/timer.h"


uint8_t* fontTop;
               
uint16_t M_TOP = 0;                     
uint16_t M_BOTTOM = SC_H - 1;           

#define SCSIZE    (SC_W * SC_H) 
#define SP_W      (SC_W * CH_W)
#define SP_H      (SC_H * CH_H)
#define MAX_CH_X  (CH_W - 1)     
#define MAX_CH_Y  (CH_H - 1)     
#define MAX_SC_X  (SC_W - 1)     
#define MAX_SC_Y  (SC_H - 1)    
#define MAX_SP_X  (SP_W - 1)     
#define MAX_SP_Y  (SP_H - 1)     

typedef struct {
    uint8_t Bold  : 1;      // 1
    uint8_t Faint  : 1;     // 2
    uint8_t Italic : 1;     // 3
    uint8_t Underline : 1;  // 4
    uint8_t Blink : 1;      // 5 (Slow Blink)
    uint8_t RapidBlink : 1; // 6
    uint8_t Reverse : 1;    // 7
    uint8_t Conceal : 1;    // 8
  }TATTR ;
  
  typedef union {
    uint8_t value;
    TATTR Bits;
  }ATTR ;





typedef struct {
    uint8_t Foreground : 4;
    uint8_t Background : 4;
}TCOLOR ;
typedef union {
    uint8_t value;
    TCOLOR Color;
}COLOR ;
  

typedef struct {
    unsigned int Reserved2   : 1;
    unsigned int Reserved4   : 1;
    unsigned int Reserved12  : 1;
    unsigned int CrLf        : 1;
    unsigned int Reserved33  : 1;
    unsigned int Reserved34  : 1;
    unsigned int Reverse     : 2;
} TMODE;


typedef union {
    uint8_t value;
    TMODE Flgs;
} MODE ;
  
  typedef struct {
    unsigned int Reserved1 : 1;     // 1 DECCKM (Cursor Keys Mode)
    unsigned int Reserved2 : 1;     // 2 DECANM (ANSI/VT52 Mode)
    unsigned int Reserved3 : 1;     // 3 DECCOLM (Column Mode)
    unsigned int Reserved4 : 1;     // 4 DECSCLM (Scrolling Mode)
    unsigned int ScreenReverse : 1; // 5 DECSCNM (Screen Mode)
    unsigned int Reserved6 : 1;     // 6 DECOM (Origin Mode)
    unsigned int WrapLine  : 1;     // 7 DECAWM (Autowrap Mode)
    unsigned int Reserved8 : 1;     // 8 DECARM (Auto Repeat Mode)
    unsigned int Reserved9 : 1;     // 9 DECINLM (Interlace Mode)
    unsigned int InsertMode:1;     // 10 DECIM (Insert Mode)
    unsigned int Reverse : 6;    
}TMODE_EX ;
  
typedef union {
    uint16_t value;
    TMODE_EX Flgs;
}MODE_EX ;

char outputBuf[30]={0};
int outputLen = 0;
uint8_t screen[SCSIZE];      
uint8_t attrib[SCSIZE];      
uint8_t colors[SCSIZE];      
uint8_t tabs[SC_W];  
uint8_t *fb;
const uint8_t *currentTextTable;
#define NONE 0
#define ES   1
#define CSI  2
#define CSI2 3
#define LSC  4
#define G0S  5
#define G1S  6

static const uint8_t defaultMode = 0b00001000;
static const uint16_t defaultModeEx = 0b0000000001000000;
static const ATTR defaultAttr = {0b00000000};
static const COLOR defaultColor = {(clBlack << 4) | clWhite}; // back, fore
uint8_t escMode = NONE;         // esc mode indicator
bool isShowCursor = false;     // is the cursor shown in last call?
bool canShowCursor = true;    // can the cursor be shown?
bool hasParam = false;         // <ESC> [ has parameters
bool isDECPrivateMode = false; // DEC Private Mode (<ESC> [ ?)
MODE mode;
//mode.value = defaultMode;
MODE_EX mode_ex;
//mode_ex.value = defaultModeEx;

int16_t p_XP = 0;
int16_t p_YP = 0;

int16_t XP = 0;
int16_t YP = 0;
ATTR cAttr ;
COLOR cColor ;

int16_t b_XP = 0;
int16_t b_YP = 0;
ATTR bAttr ;
COLOR bColor ;

int16_t nVals = 0;
int16_t vals[10] = {0};
static repeating_timer_t cursor_timer;


bool dispCursor(repeating_timer_t *rt) ;  



//static void scroll_framebuffer(uint8_t *fb,  int scroll_y1, int scroll_y2, int n, uint8_t bg_color);
static void fill_rect_4bpp(uint8_t *fb,  int x, int y, int w, int h, uint8_t color);
static void drawTxt6x8(uint8_t *fb,uint8_t c,int x0,int y0, uint8_t color);
static void setpixel(uint8_t *fb,int32_t x, int32_t y,uint8_t color);
static void sc_updateChar(uint16_t x, uint16_t y);
static  void drawCursor(uint16_t x, uint16_t y); 
static void sc_updateLine(uint16_t ln); 
static void setCursorToHome(void);
static void initCursorAndAttribute(void);
static void scroll(void);
static void clearParams(uint8_t m);
static void saveCursor(void);
static void restoreCursor(void);
static void keypadApplicationMode(void);
static void keypadNumericMode(void);
static void vindex(int16_t v);
static void nextLine(void) ;
static void horizontalTabulationSet(void);
static void reverseIndex(int16_t v);
static void identify(void);
static void resetToInitialState(void);
//static void cursorUp(int16_t v);
static void cursorDown(int16_t v);
static void cursorPosition(uint8_t y, uint8_t x);
static void refreshScreen(void);
static void eraseInDisplay(uint8_t m);
static void eraseInLine(uint8_t m);
static void insertLine(uint8_t v);
static void deleteLine(uint8_t v) ;
static void cursorPositionReport(uint16_t y, uint16_t x);
static void deviceAttributes(uint8_t m);
static void tabulationClear(uint8_t m);
static void lineMode(bool m);
static void screenMode(bool m);
static void autoWrapMode(bool m);
static void setMode(int16_t *vals, int16_t nVals);
static void decSetMode(int16_t *vals, int16_t nVals);
static void resetMode(int16_t *vals, int16_t nVals);
static void decResetMode(int16_t *vals, int16_t nVals);
static void selectGraphicRendition(int16_t *vals, int16_t nVals);
static void deviceStatusReport(uint8_t m);
static void loadLEDs(uint8_t m);
static void setTopAndBottomMargins(int16_t s, int16_t e);
static void invokeConfidenceTests(uint8_t m);
static void doubleHeightLine_TopHalf(void);
static void doubleHeightLine_BotomHalf(void);
static void singleWidthLine(void);
static void doubleWidthLine(void);
static void screenAlignmentDisplay(void);
static void setG0charset(char c);
static void setG1charset(char c);
static void unknownSequence(uint8_t m, char c) ;
static void cursorForward(int16_t v);
static void cursorBackward(int16_t v);

static void setpixel(uint8_t *fb,int32_t x, int32_t y,uint8_t color){
    uint8_t *pixel = &((uint8_t *)fb)[(x + (SC_PIXEL_WIDTH*y))>>1];
  
    if (x&0x01) {
      *pixel = ((uint8_t)color & 0x0f) | (*pixel & 0xf0);
    } else {
      *pixel = ((uint8_t)color << 4) | (*pixel & 0x0f);
    }
  }
static void sc_updateChar(uint16_t x, uint16_t y) {
    uint16_t idx = SC_W * y + x;
    uint8_t c    = screen[idx];        
    ATTR a;
    COLOR l;
    a.value = attrib[idx];             
    l.value = colors[idx];             
    uint8_t fore = l.Color.Foreground | (a.Bits.Blink << 3);
    uint8_t back = l.Color.Background | (a.Bits.Blink << 3);
    if (a.Bits.Reverse){
        uint8_t temp = fore; fore = back; back = temp;
    } 
    if (mode_ex.Flgs.ScreenReverse){
        uint8_t temp = fore; fore = back; back = temp;
    } 
    uint16_t xx = x * CH_W;
    uint16_t yy = y * CH_H;
    fill_rect_4bpp(fb, xx, yy, CH_W, CH_H, back);
    drawTxt6x8(fb,c,xx,yy, fore);
    if (a.Bits.Bold){
        drawTxt6x8(fb,c,xx+1,yy, fore);
    }
        
}

    
  

static  void drawCursor(uint16_t x, uint16_t y) {
    uint16_t xx = x * CH_W;
    uint16_t yy = y * CH_H;
    fill_rect_4bpp(fb, xx, yy, CH_W, CH_H, clWhite);
}

bool dispCursor(repeating_timer_t *rt) {
    if (escMode != NONE)
      return true;
    sc_updateChar(p_XP, p_YP);  
    if  (canShowCursor){
        isShowCursor = !isShowCursor;
        if (isShowCursor){
            drawCursor(XP, YP);
        }
        p_XP = XP;
        p_YP = YP;
    }
    return true;
}

static void sc_updateLine(uint16_t ln) {
    for (uint32_t i=0;i<SC_W;i++){
       sc_updateChar(i, ln);
    }
}
    
static void setCursorToHome(void) {
    XP = 0;
    YP = 0;
}

static void initCursorAndAttribute(void) {
    cAttr.value = defaultAttr.value;
    cColor.value = defaultColor.value;
    memset(tabs, 0x00, SC_W);
    for (uint8_t i = 0; i < SC_W; i += 8)
      tabs[i] = 1;
    setTopAndBottomMargins(1, SC_H);
    mode.value = defaultMode;
    mode_ex.value = defaultModeEx;
}
static void scroll(void) {
  if (mode.Flgs.CrLf) XP = 0;
  YP++;

  if (YP > M_BOTTOM) {
      int lines_to_scroll = M_BOTTOM - M_TOP;

      if (lines_to_scroll > 0) {
          size_t copy_bytes = lines_to_scroll * SC_W;
          int dst = M_TOP * SC_W;
          int src = (M_TOP + 1) * SC_W;

          memmove(&screen[dst], &screen[src], copy_bytes);
          memmove(&attrib[dst], &attrib[src], copy_bytes);
          memmove(&colors[dst], &colors[src], copy_bytes);
      }


      int bottom_idx = M_BOTTOM * SC_W;
      memset(&screen[bottom_idx], 0, SC_W);
      memset(&attrib[bottom_idx], defaultAttr.value, SC_W);
      memset(&colors[bottom_idx], defaultColor.value, SC_W);

      YP = M_BOTTOM;

      for (uint8_t y = M_TOP; y <= M_BOTTOM; y++)
          sc_updateLine(y);
  }
}
/*
static void scroll(void) {
  if (mode.Flgs.CrLf) XP = 0;
  YP++;
  if (YP > M_BOTTOM) {
    uint16_t n = SCSIZE - SC_W - ((M_TOP + MAX_SC_Y - M_BOTTOM) * SC_W);
    uint16_t idx = SC_W * M_BOTTOM;
    uint16_t idx2;
    uint16_t idx3 = M_TOP * SC_W;
    memmove(&screen[idx3], &screen[idx3 + SC_W], n);
    memmove(&attrib[idx3], &attrib[idx3 + SC_W], n);
    memmove(&colors[idx3], &colors[idx3 + SC_W], n);
    for (uint8_t x = 0; x < SC_W; x++) {
      idx2 = idx + x;
      screen[idx2] = 0;
      attrib[idx2] = defaultAttr.value;
      colors[idx2] = defaultColor.value;
    }
    
    YP = M_BOTTOM;
  }
  for (uint8_t y = 0; y <SC_H; y++)//for (uint8_t y = M_TOP; y <=M_BOTTOM; y++)
      sc_updateLine(y);
}
*/
/*
static void scroll(void) {
    if (mode.Flgs.CrLf) XP = 0;
    if (YP+1 > M_BOTTOM) {
      YP = M_BOTTOM;  
      uint16_t n = SCSIZE - SC_W - ((M_TOP + MAX_SC_Y - M_BOTTOM) * SC_W);
      uint16_t idx = SC_W * M_BOTTOM;
      uint16_t idx2;
      uint16_t idx3 = M_TOP * SC_W;
      memmove(&screen[idx3], &screen[idx3 + SC_W], n);
      memmove(&attrib[idx3], &attrib[idx3 + SC_W], n);
      memmove(&colors[idx3], &colors[idx3 + SC_W], n);
      for (uint8_t x = 0; x < SC_W; x++) {
        idx2 = idx + x;
        screen[idx2] = 0;
        attrib[idx2] = defaultAttr.value;
        colors[idx2] = defaultColor.value;
      }
      scroll_framebuffer(fb, M_TOP*CH_H, (M_BOTTOM+1)*CH_H-1, CH_H, clBlack);
      
    }else{
        YP++;
    }
    for (uint8_t y = M_TOP; y <= M_BOTTOM; y++){
      sc_updateLine(y);
    }
      
}
*/

static void clearParams(uint8_t m) {
    escMode = m;
    isDECPrivateMode = false;
    nVals = 0;
    vals[0] = vals[1] = vals[2] = vals[3] = 0;
    hasParam = false;
}


static mp_obj_t vt_printChar(mp_obj_t value_obj) {
    int c = mp_obj_get_int(value_obj);
    // [ESC] キー
    if (c == 0x1b) {
      escMode = ES;   // esc mode start
      return mp_const_none;
    }
    // エスケープシーケンス
    if (escMode == ES) {
      switch (c) {
        case '[':
          // Control Sequence Introducer (CSI) 
          clearParams(CSI);
          break;
        case '#':
          // Line Size Command  
          clearParams(LSC);
          break;
        case '(':
          // G0 
          clearParams(G0S);
          break;
        case ')':
          // G1 
          clearParams(G1S);
          break;
        default:
          // <ESC> xxx: 
          switch (c) {
            case '7':
              // DECSC (Save Cursor): save cursor position 
              saveCursor();
              break;
            case '8':
              // DECRC (Restore Cursor): 
              restoreCursor();
              break;
            case '=':
              // DECKPAM (Keypad Application Mode): 
              keypadApplicationMode();
              break;
            case '>':
              // DECKPNM (Keypad Numeric Mode):
              keypadNumericMode();
              break;
            case 'D':
              // IND (Index): one line down
              vindex(1);
              break;
            case 'E':
              // NEL (Next Line): 
              nextLine();
              break;
            case 'H':
              // HTS (Horizontal Tabulation Set): 
              horizontalTabulationSet();
              break;
            case 'M':
              // RI (Reverse Index): 
              reverseIndex(1);
              break;
            case 'Z':
              // DECID (Identify): 
              identify();
              break;
            case 'c':
              // RIS (Reset To Initial State): 
              resetToInitialState();
              break;
            default:
              // not decodeable
              unknownSequence(escMode, c);
              break;
          }
          clearParams(NONE);
          break;
      }
      return mp_const_none;
    }
  
    // "[" Control Sequence Introducer (CSI)
    int16_t v1 = 0;
    int16_t v2 = 0;
  
    if (escMode == CSI) {
      escMode = CSI2;
      isDECPrivateMode = (c == '?');
      if (isDECPrivateMode) return mp_const_none;
    }
  
    if (escMode == CSI2) {
      if (isdigit(c)) {
        // [パラメータ]
        vals[nVals] = vals[nVals] * 10 + (c - '0');
        hasParam = true;
      } else if (c == ';') {
        // [セパレータ]
        nVals++;
        hasParam = false;
      } else {
        if (hasParam) nVals++;
        switch (c) {
          case 'A':
            // CUU (Cursor Up): 
            v1 = (nVals == 0) ? 1 : vals[0];
            reverseIndex(v1);
            break;
          case 'B':
            // CUD (Cursor Down): 
            v1 = (nVals == 0) ? 1 : vals[0];
            cursorDown(v1);
            break;
          case 'C':
            // CUF (Cursor Forward): 
            v1 = (nVals == 0) ? 1 : vals[0];
            cursorForward(v1);
            break;
          case 'D':
            // CUB (Cursor Backward): 
            v1 = (nVals == 0) ? 1 : vals[0];
            cursorBackward(v1);
            break;
          case 'H':
          // CUP (Cursor Position): 
          case 'f':
            // HVP (Horizontal and Vertical Position): 
            v1 = (nVals == 0) ? 1 : vals[0];
            v2 = (nVals <= 1) ? 1 : vals[1];
            cursorPosition(v1, v2);
            break;
          case 'J':
            // ED (Erase In Display): 
            v1 = (nVals == 0) ? 0 : vals[0];
            eraseInDisplay(v1);
            break;
          case 'K':
            // EL (Erase In Line) 
            v1 = (nVals == 0) ? 0 : vals[0];
            eraseInLine(v1);
            break;
          case 'L':
            // IL (Insert Line): 
            v1 = (nVals == 0) ? 1 : vals[0];
            insertLine(v1);
            break;
          case 'M':
            // DL (Delete Line): 
            v1 = (nVals == 0) ? 1 : vals[0];
            deleteLine(v1);
            break;
          case 'c':
            // DA (Device Attributes): 
            v1 = (nVals == 0) ? 0 : vals[0];
            deviceAttributes(v1);
            break;
          case 'g':
            // TBC (Tabulation Clear): 
            v1 = (nVals == 0) ? 0 : vals[0];
            tabulationClear(v1);
            break;
          case 'h':
            if (isDECPrivateMode) {
              // DECSET (DEC Set Mode):
              decSetMode(vals, nVals);
            } else {
              // SM (Set Mode): 
              setMode(vals, nVals);
            }
            break;
          case 'l':
            if (isDECPrivateMode) {
              // DECRST (DEC Reset Mode): 
              decResetMode(vals, nVals);
            } else {
              // RM (Reset Mode): 
              resetMode(vals, nVals);
            }
            break;
          case 'm':
            // SGR (Select Graphic Rendition): 
            if (nVals == 0)
              nVals = 1; // vals[0] = 0
            selectGraphicRendition(vals, nVals);
            break;
          case 'n':
            // DSR (Device Status Report): 
            v1 = (nVals == 0) ? 0 : vals[0];
            deviceStatusReport(v1);
            break;
          case 'q':
            // DECLL (Load LEDS): 
            v1 = (nVals == 0) ? 0 : vals[0];
            loadLEDs(v1);
            break;
          case 'r':
            // DECSTBM (Set Top and Bottom Margins): 
            v1 = (nVals == 0) ? 1 : vals[0];
            v2 = (nVals <= 1) ? SC_H : vals[1];
            setTopAndBottomMargins(v1, v2);
            break;
          case 'y':
            // DECTST (Invoke Confidence Test): 
            if ((nVals > 1) && (vals[0] = 2))
              invokeConfidenceTests(vals[1]);
            break;
          default:
            // unknown command
            unknownSequence(escMode, c);
            break;
        }
        clearParams(NONE);
      }
      return mp_const_none;
    }else if (escMode == LSC) {
      switch (c) {
        case '3':
          // DECDHL (Double Height Line): 
          doubleHeightLine_TopHalf();
          break;
        case '4':
          // DECDHL (Double Height Line): 
          doubleHeightLine_BotomHalf();
          break;
        case '5':
          // DECSWL (Single-width Line): 
          singleWidthLine();
          break;
        case '6':
          // DECDWL (Double-Width Line): 
          doubleWidthLine();
          break;
        case '8':
          // DECALN (Screen Alignment Display): 
          screenAlignmentDisplay();
          break;
        default:
          // 未確認のシーケンス
          unknownSequence(escMode, c);
          break;
      }
      clearParams(NONE);
      return mp_const_none;
    }else if (escMode == G0S) {
      // SCS (Select Character Set): G0 
      setG0charset(c);
      clearParams(NONE);
      return mp_const_none;
    }else if(escMode == G1S) {
      // SCS (Select Character Set): G1 
      setG1charset(c);
      clearParams(NONE);
      return mp_const_none;
    }
  

    if ((c == 0x0a) || (c == 0x0b) || (c == 0x0c)) {
      scroll();
      return mp_const_none;
    }
  
    // 復帰 (CR)
    if (c == 0x0d) {
      XP = 0;
      return mp_const_none;
    }
  
    // バックスペース (BS)
    if (c == 0x7f) {
      cursorBackward(1);
      uint16_t idx = YP * SC_W + XP;
      screen[idx] = 0;
      attrib[idx] = 0;
      colors[idx] = cColor.value;
      sc_updateChar(XP, YP);
      return mp_const_none;
    }
    if (c == 0x08) {
      cursorBackward(1);
      return mp_const_none;
    }
    // タブ (TAB)
    if (c == 0x09) {
      int16_t idx = -1;
      for (int16_t i = XP + 1; i < SC_W; i++) {
        if (tabs[i]) {
          idx = i;
          break;
        }
      }
      XP = (idx == -1) ? MAX_SC_X : idx;
      return mp_const_none;
    }
  
    // 通常文字
    if (XP < SC_W) {
      uint16_t idx = YP * SC_W + XP;
      if (mode_ex.Flgs.InsertMode){
        // 挿入モード
        for (int16_t i = (YP+1) * SC_W - 1; i > idx; i--) {
          screen[i] = screen[i - 1];
          attrib[i] = attrib[i - 1];
          colors[i] = colors[i - 1];
        }
        screen[idx] = c;
        attrib[idx] = cAttr.value;
        colors[idx] = cColor.value;
        for (int16_t i = XP; i < SC_W; i++) {
          sc_updateChar(i, YP);
        }
      }else{
        screen[idx] = c;
        attrib[idx] = cAttr.value;
        colors[idx] = cColor.value;
        sc_updateChar(XP, YP);
      }
      
    }
  
 
    // 折り返し行
    if (XP+1>=SC_W){
        if (mode_ex.Flgs.WrapLine){
            XP=0;
            scroll();
        }
            
        else{
            XP = MAX_SC_X;
        }
            
    }else{
        XP++;
    }

    
    return mp_const_none;
}

static MP_DEFINE_CONST_FUN_OBJ_1(vt_printChar_obj, vt_printChar);  





static void saveCursor(void) {
    b_XP = XP;
    b_YP = YP;
    bAttr.value = cAttr.value;
    bColor.value = cColor.value;
}
  
  // DECRC (Restore Cursor): 
static void restoreCursor(void){
    XP = b_XP;
    YP = b_YP;
    cAttr.value = bAttr.value;
    cColor.value = bColor.value;
}
  
  // DECKPAM (Keypad Application Mode): 
static void keypadApplicationMode(void) {
    return;
  }
  
  // DECKPNM (Keypad Numeric Mode): 
static void keypadNumericMode(void) {
    return;
}




  // IND (Index): 

static void vindex(int16_t v) {
    cursorDown(v);
}

// NEL (Next Line): 

static void nextLine(void) {
    scroll();
}
  
  // HTS (Horizontal Tabulation Set): 
static void horizontalTabulationSet(void) {
    tabs[XP] = 1;
  }
  
  // RI (Reverse Index): 

static void reverseIndex(int16_t v) {
    //cursorUp(v);
    if ((YP - v) < M_TOP) {
        // Scroll down the scroll region by v lines
        int lines_to_scroll = v;
        if (lines_to_scroll > (M_BOTTOM - M_TOP + 1))
            lines_to_scroll = (M_BOTTOM - M_TOP + 1);

        int lines_to_move = (M_BOTTOM - M_TOP + 1) - lines_to_scroll;

        if (lines_to_move > 0) {
            int n = SC_W * lines_to_move;
            int dst = SC_W * (M_TOP + lines_to_scroll);
            int src = SC_W * M_TOP;
            memmove(&screen[dst], &screen[src], n);
            memmove(&attrib[dst], &attrib[src], n);
            memmove(&colors[dst], &colors[src], n);
        }

        // Fill new top lines
        int top_idx = SC_W * M_TOP;
        int fill_len = SC_W * lines_to_scroll;
        memset(&screen[top_idx], 0x00, fill_len);
        memset(&attrib[top_idx], defaultAttr.value, fill_len);
        memset(&colors[top_idx], defaultColor.value, fill_len);

        YP = M_TOP;
        for (uint8_t y = M_TOP; y <= M_BOTTOM; y++)
            sc_updateLine(y);
    } else {
        YP -= v;
    }
  }
  
  // DECID (Identify): 
static void identify(void) {
    deviceAttributes(0); // same as DA (Device Attributes)
  }
  
  // RIS (Reset To Initial State) リセット
static void resetToInitialState(void) {
    fill_rect_4bpp(fb,  0, 0, SC_PIXEL_WIDTH, SC_PIXEL_HEIGHT, defaultColor.Color.Background);
    initCursorAndAttribute();
    eraseInDisplay(2);
  }


// "[" Control Sequence Introducer (CSI) 
// -----------------------------------------------------------------------------

// CUU (Cursor Up): 

/* 
static void cursorUp(int16_t v) {
    if ((YP - v) <= M_TOP){
        YP = M_TOP;
    }else{
        YP -= v;
    }
  }
*/  
  // CUD (Cursor Down): 

static void cursorDown(int16_t v) {

    if ((YP+v)>M_BOTTOM){
        YP = M_BOTTOM;
    }else{
        YP += v;
    }
  }
  
  // CUF (Cursor Forward): 
static void cursorForward(int16_t v) {
    if ((XP+v)>=SC_W){
        XP = MAX_SC_X;
    }else{
        XP += v;
    }
  }
  
  // CUB (Cursor Backward): 
  void cursorBackward(int16_t v) {
    if ((XP-v)<0){
        XP=0;
    }else{
        XP -=v;
    }
  }
  
  // CUP (Cursor Position): 
  // HVP (Horizontal and Vertical Position): 
static void cursorPosition(uint8_t y, uint8_t x) {

    if ((y-1)>=SC_H){
        YP = MAX_SC_Y;
    }else{
        YP= y-1;
    }

    if ((x-1)>=SC_W){
        XP = MAX_SC_X;
    }else{
        XP = x -1;
    }

}
  

static void refreshScreen(void) {

    for (uint8_t i = 0; i < SC_H; i++){
        sc_updateLine(i);
    }
}
  

static void eraseInDisplay(uint8_t m) {
    uint8_t sl = 0, el = 0;
    uint16_t idx = 0, n = 0;
  
    switch (m) {
      case 0:

        sl = YP;
        el = MAX_SC_Y;
        idx = YP * SC_W + XP;
        n   = SCSIZE - (YP * SC_W + XP);
        break;
      case 1:

        sl = 0;
        el = YP;
        idx = 0;
        n = YP * SC_W + XP + 1;
        break;
      case 2:

        sl = 0;
        el = MAX_SC_Y;
        idx = 0;
        n = SCSIZE;
        break;
    }
  
    if (m <= 2) {
      memset(&screen[idx], 0x00, n);
      memset(&attrib[idx], defaultAttr.value, n);
      memset(&colors[idx], defaultColor.value, n);
      for (uint8_t i = sl; i <= el; i++)
        sc_updateLine(i);
    }
  }
  
  // EL (Erase In Line): 
static void eraseInLine(uint8_t m) {
    uint16_t slp = 0, elp = 0;
  
    switch (m) {
      case 0:
        // current to end
        slp = YP * SC_W + XP;
        elp = YP * SC_W + MAX_SC_X;
        break;
      case 1:
        // start to current
        slp = YP * SC_W;
        elp = YP * SC_W + XP;
        break;
      case 2:
        // whole line
        slp = YP * SC_W;
        elp = YP * SC_W + MAX_SC_X;
        break;
    }
  
    if (m <= 2) {
      uint16_t n = elp - slp + 1;
      memset(&screen[slp], 0x00, n);
      memset(&attrib[slp], defaultAttr.value, n);
      memset(&colors[slp], cColor.value, n);
      //memset(&colors[slp], defaultColor.value, n);
      sc_updateLine(YP);
    }
}
  
  // IL (Insert Line): 

static void insertLine(uint8_t v) {
    int16_t rows = v;
    if (rows == 0) return;
    if (rows > ((M_BOTTOM + 1) - YP)) rows = (M_BOTTOM + 1) - YP;
    int16_t idx = SC_W * YP;
    int16_t n = SC_W * rows;
    int16_t idx2 = idx + n;
    int16_t move_rows = (M_BOTTOM + 1) - YP - rows;
    int16_t n2 = SC_W * move_rows;
  
    if (move_rows > 0) {
      memmove(&screen[idx2], &screen[idx], n2);
      memmove(&attrib[idx2], &attrib[idx], n2);
      memmove(&colors[idx2], &colors[idx], n2);
    }
    memset(&screen[idx], 0x00, n);
    memset(&attrib[idx], defaultAttr.value, n);
    memset(&colors[idx], defaultColor.value, n);
    for (uint8_t y = YP; y <= M_BOTTOM; y++)
      sc_updateLine(y);
  }
  
  // DL (Delete Line): 

static  void deleteLine(uint8_t v) {
    int16_t rows = v;
    if (rows == 0) return;
    if (rows > ((M_BOTTOM + 1) - YP)) rows = (M_BOTTOM + 1) - YP;
    int16_t idx = SC_W * YP;
    int16_t n = SC_W * rows;
    int16_t idx2 = idx + n;
    int16_t move_rows = (M_BOTTOM + 1) - YP - rows;
    int16_t n2 = SC_W * move_rows;
    int16_t idx3 = (M_BOTTOM + 1) * SC_W - n;
  
    if (move_rows > 0) {
      memmove(&screen[idx], &screen[idx2], n2);
      memmove(&attrib[idx], &attrib[idx2], n2);
      memmove(&colors[idx], &colors[idx2], n2);
    }
    memset(&screen[idx3], 0x00, n);
    memset(&attrib[idx3], defaultAttr.value, n);
    memset(&colors[idx3], defaultColor.value, n);
    for (uint8_t y = YP; y <= M_BOTTOM; y++)
      sc_updateLine(y);
  }
  
  // CPR (Cursor Position Report): 
static void cursorPositionReport(uint16_t y, uint16_t x) {
    char temp[30];
    int32_t len = sprintf(temp, "\x1b[%d;%dR", SC_H, SC_W);
    
    if (outputLen + len <= sizeof(outputBuf)) {
        memcpy(&(outputBuf[outputLen]), temp, len);
        outputLen += len;
    }
}
  
  // DA (Device Attributes): 

static void deviceAttributes(uint8_t m) {

    if (outputLen + 7 <= sizeof(outputBuf)) {
        memcpy(&(outputBuf[outputLen]), "\e[?1;0c", 7);
        outputLen += 7;
      }
  }
  
  // TBC (Tabulation Clear): 
static void tabulationClear(uint8_t m) {
    switch (m) {
      case 0:
        // current position
        tabs[XP] = 0;
        break;
      case 3:
        // all tabs
        memset(tabs, 0x00, SC_W);
        break;
    }
  }

  // LNM (Line Feed / New Line Mode): 
static void lineMode(bool m) {
    mode.Flgs.CrLf = m;
  }
  
  // DECSCNM (Screen Mode):  
static void screenMode(bool m) {
    mode_ex.Flgs.ScreenReverse = m;
    refreshScreen();
  }
  
  // DECAWM (Auto Wrap Mode): 
static void autoWrapMode(bool m) {
    mode_ex.Flgs.WrapLine = m;
  }
  
  // SM (Set Mode): 
static void setMode(int16_t *vals, int16_t nVals) {
    for (int16_t i = 0; i < nVals; i++) {
      switch (vals[i]) {
        case 20:
          // LNM (Line Feed / New Line Mode)
          lineMode(true);
          break;
        case 4:
          // IRM (Insert Mode): 
          mode_ex.Flgs.InsertMode = 1;
          break;
        default:
          break;
      }
    }
  }
  
  // DECSET (DEC Set Mode): 
static void decSetMode(int16_t *vals, int16_t nVals) {
    for (int16_t i = 0; i < nVals; i++) {
      switch (vals[i]) {
        case 5:
          // DECSCNM (Screen Mode): 
          screenMode(true);
          break;
        case 7:
          // DECAWM (Auto Wrap Mode):
          autoWrapMode(true);
          break;

        case 25:
          // DECTCEM (Cursor Mode): 
          canShowCursor = true;
          break;
        default:
          break;
      }
    }
  }
  
  // RM (Reset Mode): 
static void resetMode(int16_t *vals, int16_t nVals) {
    for (int16_t i = 0; i < nVals; i++) {
      switch (vals[i]) {
        case 20:
          // LNM (Line Feed / New Line Mode)
          lineMode(false);
          break;

        case 4:
          // IRM (Insert Mode): 
          mode_ex.Flgs.InsertMode = 0;
          break;
        default:
          break;
      }
    }
  }
  
  // DECRST (DEC Reset Mode): 
static void decResetMode(int16_t *vals, int16_t nVals) {
    for (int16_t i = 0; i < nVals; i++) {
      switch (vals[i]) {
        case 5:
          // DECSCNM (Screen Mode): 
          screenMode(false);
          break;
        case 7:
          // DECAWM (Auto Wrap Mode): 
          autoWrapMode(false);
          break;
        case 25:
          // DECTCEM (Cursor Mode): 
          canShowCursor = false;
          break;
        default:
          break;
      }
    }
  }
  
  // SGR (Select Graphic Rendition): 
static void selectGraphicRendition(int16_t *vals, int16_t nVals) {
    uint8_t seq = 0;
    uint16_t r, g, b, cIdx;
    bool isFore = true;
    for (int16_t i = 0; i < nVals; i++) {
      int16_t v = vals[i];
      switch (seq) {
        case 0:
          switch (v) {
            case 0:
                // Reset all attributes
              cAttr.value = 0;
              cColor.value = defaultColor.value;
              break;
            case 1:
              // Bold
              cAttr.Bits.Bold = 1;
              break;
            case 4:
              // char with underline
              cAttr.Bits.Underline = 1;
              break;
            case 5:
              // blink
              cAttr.Bits.Blink = 1;
              break;
            case 7:
              // reverse
              cAttr.Bits.Reverse = 1;
              break;
            case 21:
              // bold
              cAttr.Bits.Bold = 0;
              break;
            case 22:
              // bold remove
              cAttr.Bits.Bold = 0;
              break;
            case 24:
              // char with underline remove
              cAttr.Bits.Underline = 0;
              break;
            case 25:
              // blink remove
              cAttr.Bits.Blink = 0;
              break;
            case 27:
              // inverse remove
              cAttr.Bits.Reverse = 0;
              break;
            case 38:
              seq = 1;
              isFore = true;
              break;
            case 39:
              // front color recover
              cColor.Color.Foreground = defaultColor.Color.Foreground;
              break;
            case 48:
              seq = 1;
              isFore = false;
              break;
            case 49:
              // background recover
              cColor.Color.Background = defaultColor.Color.Background;
              break;
            default:
              if (v >= 30 && v <= 37) {
                //front color
                cColor.Color.Foreground = v - 30;
              } else if (v >= 40 && v <= 47) {
                // background color
                cColor.Color.Background = v - 40;
              }
              break;
          }
          break;
        case 1:
          switch (v) {
            case 2:
              // RGB
              seq = 3;
              break;
            case 5:
              // Color Index
              seq = 2;
              break;
            default:
              seq = 0;
              break;
          }
          break;
        case 2:
          // Index Color
          if (v < 256) {
            if (v < 16) {
              // 16 color
              cIdx = v;
            } else if (v < 232) {
              // 6x6x6 RGB 
              b = ( (v - 16)       % 6) / 3;
              g = (((v - 16) /  6) % 6) / 3;
              r = (((v - 16) / 36) % 6) / 3;
              cIdx = (b << 2) | (g << 1) | r;
            } else {
              // 244 color
              if (v < 244)
                cIdx = clBlack;
              else
                cIdx = clWhite;
            }
            if (isFore)
              cColor.Color.Foreground = cIdx;
            else
              cColor.Color.Background = cIdx;
          }
          seq = 0;
          break;
        case 3:
          // RGB - R
          seq = 4;
          break;
        case 4:
          // RGB - G
          seq = 5;
          break;
        case 5:
          // RGB - B
          if (vals[i-2]>128){
            r = 1;
          }else{
            r=0;
        }
        if (vals[i-1]>128){
            g = 1;
          }else{
            g=0;
        }
        if (vals[i-0]>128){
            b = 1;
          }else{
            b=0;
        }
          cIdx = (b << 2) | (g << 1) | r;
          if (isFore)
            cColor.Color.Foreground = cIdx;
          else
            cColor.Color.Background = cIdx;
          seq = 0;
          break;
        default:
          seq = 0;
          break;
      }
    }
}
  
  // DSR (Device Status Report): 
static void deviceStatusReport(uint8_t m) {
    switch (m) {
      case 5:
        if (outputLen + 4 <= sizeof(outputBuf)) {
          memcpy(&(outputBuf[outputLen]), "\e[0n", 4);
          outputLen += 4;
        }

        break;
      case 6:
        cursorPositionReport(XP, YP); // CPR (Cursor Position Report)
        break;
    }
  }

  // DECLL (Load LEDS): 
static  void loadLEDs(uint8_t m) {
    return;
    
  }
  
  // DECSTBM (Set Top and Bottom Margins): 
static  void setTopAndBottomMargins(int16_t s, int16_t e) {
    if (e <= s) return;
    M_TOP    = s - 1;
    if (M_TOP > MAX_SC_Y) M_TOP = MAX_SC_Y;
    M_BOTTOM = e - 1;
    if (M_BOTTOM > MAX_SC_Y) M_BOTTOM = MAX_SC_Y;
    setCursorToHome();
  }
  
  // DECTST (Invoke Confidence Test): 
static void invokeConfidenceTests(uint8_t m) {
     return;
}

  // "]" Operating System Command (OSC) 
  // -----------------------------------------------------------------------------
  
  // "#" Line Size Command  
  // -----------------------------------------------------------------------------
  
  // DECDHL (Double Height Line): 
static void doubleHeightLine_TopHalf(void) {
    return;
  }
  
  // DECDHL (Double Height Line): 
static  void doubleHeightLine_BotomHalf(void) {
    return;
  }
  
  // DECSWL (Single-width Line): 
static void singleWidthLine(void) {
    return;
  }
  
  // DECDWL (Double-Width Line): 
static void doubleWidthLine(void) {
    return;
  }
  
  // DECALN (Screen Alignment Display): 
static  void screenAlignmentDisplay(void) {
    
    memset(screen, 0x45, SCSIZE);
    memset(attrib, defaultAttr.value, SCSIZE);
    memset(colors, defaultColor.value, SCSIZE);
    for (uint8_t y = 0; y < SC_H; y++)
      sc_updateLine(y);
  }
  
  // "(" G0 Sets Sequence
  // -----------------------------------------------------------------------------
  
  // G0 
static  void setG0charset(char c) {
    return;
  }
  
  // "(" G1 Sets Sequence
  // -----------------------------------------------------------------------------
  
  // G1 
static void setG1charset(char c) {
    return;
  }
  
  // Unknown Sequence
  // -----------------------------------------------------------------------------
  

static void unknownSequence(uint8_t m, char c) {
    return;
  }
  







static void drawTxt6x8(uint8_t *fb,uint8_t c,int x0,int y0, uint8_t color){
  // extract arguments
    int x;
    int y;
    if (c < 32 ) {
      c = 32;
    }
      // get char data
    const uint8_t *chr_data = &currentTextTable[(c - 32) * CH_H];
      // loop over char data
    y = y0;
    for (; y < y0+CH_H; y++) {  
      if (0 <= y && y < SC_PIXEL_WIDTH) {
        x = x0;
        uint8_t line_data = *chr_data++; 
        for (;x<x0+CH_W-1;x++){
            if ((line_data&0x80)&&(0 <= x && x < SC_PIXEL_WIDTH)) { // only draw if pixel set
                setpixel(fb,x, y,color);
            }
          line_data <<= 1;
        }
      }    
    }
    x0 +=CH_W;
}


/*
static void scroll_framebuffer(uint8_t *fb, int scroll_y1, int scroll_y2, int n, uint8_t bg_color){
    int row_bytes = SC_PIXEL_WIDTH >> 1; 
    if (scroll_y1 < 0 || scroll_y2 >= SC_PIXEL_HEIGHT || n <= 0 || (scroll_y2 - scroll_y1 + 1) <= n)
        return;

    for (int y = scroll_y1; y <= scroll_y2 - n; y++) {
        uint8_t *dst_ptr = fb + y * row_bytes;
        uint8_t *src_ptr = fb + (y + n) * row_bytes;

        for (int x = 0; x < row_bytes; x += 8) {
             *dst_ptr++ = *src_ptr++;
             *dst_ptr++ = *src_ptr++;
             *dst_ptr++ = *src_ptr++;
             *dst_ptr++ = *src_ptr++;
             *dst_ptr++ = *src_ptr++;
             *dst_ptr++ = *src_ptr++;
             *dst_ptr++ = *src_ptr++;
             *dst_ptr++ = *src_ptr++;
        }
    }
    bg_color = (bg_color & 0x0F)|(bg_color<<4); //double the bg color as 2 pixels
    for (int y = scroll_y2 - n + 1; y <= scroll_y2; y++) {
        uint8_t *dst_ptr = fb + y * row_bytes;
        for (int x = 0; x < row_bytes; x += 8) {
            *dst_ptr++ = bg_color;
            *dst_ptr++ = bg_color;
            *dst_ptr++ = bg_color;
            *dst_ptr++ = bg_color;
            *dst_ptr++ = bg_color;
            *dst_ptr++ = bg_color;
            *dst_ptr++ = bg_color;
            *dst_ptr++ = bg_color;
        }
    }
}
*/
static void fill_rect_4bpp(uint8_t *fb,  int x, int y, int w, int h, uint8_t color){

    int row_bytes = SC_PIXEL_WIDTH >> 1;  
    uint8_t fill_byte = (color << 4) | (color & 0x0F);
    for (int row = y; row < y + h; row++) {
        uint8_t *row_ptr = fb + row * row_bytes;
        int pos = x;
        int pixels_to_fill = w;
        uint8_t *ptr = row_ptr + (pos >> 1);
        if (pos & 1) {
            *ptr = (*ptr & 0xF0) | (color & 0x0F);
            pos++;
            pixels_to_fill--;
            ptr = row_ptr + (pos >> 1); 
        }
        int full_bytes = pixels_to_fill >> 1;      
        int remaining_pixels = pixels_to_fill & 1;   
        while (full_bytes >= 3) {
            *ptr++ = fill_byte;
            *ptr++ = fill_byte;
            *ptr++ = fill_byte;
            full_bytes -= 3;
        }
        while (full_bytes--) {
            *ptr++ = fill_byte;
        }

        if (remaining_pixels) {
            *ptr = (*ptr & 0x0F) | (color << 4);
        }
    }
}


static mp_obj_t vtterminal_init(mp_obj_t fb_obj){

    mp_buffer_info_t buf_info;
    mp_get_buffer_raise(fb_obj, &buf_info, MP_BUFFER_READ);
    fb=(uint8_t *)buf_info.buf;

    currentTextTable=font6x8tt_2;
    resetToInitialState();
    setCursorToHome();

    //init the timer and callback
    add_repeating_timer_ms(250, dispCursor, NULL, &cursor_timer);
    return mp_const_true;
}

static MP_DEFINE_CONST_FUN_OBJ_1(vt_init_obj, vtterminal_init);



static mp_obj_t vt_read(void){
    
    mp_obj_t result = mp_obj_new_str(outputBuf, outputLen);
    outputLen = 0;
    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_0(vt_read_obj, vt_read);




static const mp_rom_map_elem_t vtterminal_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_vtterminal) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&vt_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&vt_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_printChar), MP_ROM_PTR(&vt_printChar_obj)}
};
static MP_DEFINE_CONST_DICT(vtterminal_globals, vtterminal_globals_table);


const mp_obj_module_t vtterminal_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&vtterminal_globals,
};


MP_REGISTER_MODULE(MP_QSTR_vtterminal, vtterminal_cmodule);