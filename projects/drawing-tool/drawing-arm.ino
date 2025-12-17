#include <ESP32Servo.h>
#include <math.h>

// ---------------- Pins ----------------
const int PIN_BASE = 25;
const int PIN_ELBOW = 26;
const int PIN_PEN  = 33;

// ---------------- Link lengths (mm) ----------------
const float L1 = 80.0;
const float L2 = 80.0;

// ---------------- Servos ----------------
Servo sBase, sElbow, sPen;

// ---------------- Pen angles (tune) ----------------
int PEN_UP = 40;
int PEN_DOWN = 90;

// ---------------- Home pose (tune) ----------------
int HOME_BASE_DEG  = 90;
int HOME_ELBOW_DEG = 90;

// ---------------- Servo calibration (tune) ----------------
bool INV_BASE = false;
bool INV_ELBOW = false;
float OFFSET_BASE_DEG = 0.0;
float OFFSET_ELBOW_DEG = 0.0;

// ---------------- Motion tuning ----------------
const int STEP_DELAY_MS = 25;
const float LINE_STEP_MM = 0.6f;
const float SCAN_STEP_MM = 2.0f;
const int BRANCH_FLIP_DELAY_MS = 450;

// ---- Paper corner calibration ----
const float INSET_X = 15.0f;   // mm inside from left edge
const float INSET_Y = 15.0f;   // mm inside from bottom edge

// ---- Quarter-circle settings ----
const float R = 20.0f;         // radius in mm (make smaller if needed)
const int ARC_SEGMENTS = 120;  // smoothness
const float ARC_START_DEG = 0.0f;   // 0° along +x
const float ARC_END_DEG   = 90.0f;  // 90° along +y

float ORIGIN_X = 0.0;
float ORIGIN_Y = 0.0;

float curX = 0.0, curY = 0.0;
float curTh1 = 0.0f, curTh2 = 0.0f;

// ---------- Helpers ----------
float deg2rad(float d){ return d * (float)M_PI / 180.0f; }
float rad2deg(float r){ return r * 180.0f / (float)M_PI; }

int applyServoMap(float deg, bool inv, float offset) {
  float v = deg;
  if (inv) v = 180.0f - v;
  v += offset;
  if (v < 0) v = 0;
  if (v > 180) v = 180;
  return (int)lround(v);
}

void penUp(){ sPen.write(PEN_UP); delay(160); }
void penDown(){ sPen.write(PEN_DOWN); delay(160); }

void fk(float th1, float th2, float &x, float &y){
  x = L1*cos(th1) + L2*cos(th1+th2);
  y = L1*sin(th1) + L2*sin(th1+th2);
}

bool ikSigned(float x, float y, float sign, float &th1, float &th2){
  float r2 = x*x + y*y;
  float c2 = (r2 - L1*L1 - L2*L2) / (2.0f*L1*L2);
  if (c2 < -1.0f || c2 > 1.0f) return false;

  float s2 = sign * sqrtf(fmaxf(0.0f, 1.0f - c2*c2));
  th2 = atan2(s2, c2);

  float k1 = L1 + L2*c2;
  float k2 = L2*s2;
  th1 = atan2(y,x) - atan2(k2,k1);
  return true;
}

float angleDist(float a, float b){
  float d = a - b;
  while (d > (float)M_PI) d -= 2.0f*(float)M_PI;
  while (d < -(float)M_PI) d += 2.0f*(float)M_PI;
  return fabsf(d);
}

void setJoints(float th1, float th2){
  float baseDeg  = rad2deg(th1);
  float elbowDeg = rad2deg(th2);

  int outBase  = applyServoMap(baseDeg,  INV_BASE,  OFFSET_BASE_DEG);
  int outElbow = applyServoMap(elbowDeg, INV_ELBOW, OFFSET_ELBOW_DEG);

  sBase.write(outBase);
  sElbow.write(outElbow);

  curTh1 = th1;
  curTh2 = th2;
}

bool solveIKBest(float xr, float yr, float &bestTh1, float &bestTh2){
  float th1D, th2D, th1U, th2U;
  bool okD = ikSigned(xr, yr, +1.0f, th1D, th2D);
  bool okU = ikSigned(xr, yr, -1.0f, th1U, th2U);
  if (!okD && !okU) return false;

  if (okD && !okU) { bestTh1 = th1D; bestTh2 = th2D; return true; }
  if (!okD && okU) { bestTh1 = th1U; bestTh2 = th2U; return true; }

  float dD = angleDist(th1D, curTh1) + angleDist(th2D, curTh2);
  float dU = angleDist(th1U, curTh1) + angleDist(th2U, curTh2);
  if (dD <= dU) { bestTh1 = th1D; bestTh2 = th2D; }
  else          { bestTh1 = th1U; bestTh2 = th2U; }
  return true;
}

bool moveTo(float x, float y){
  float xr = x + ORIGIN_X;
  float yr = y + ORIGIN_Y;

  float th1, th2;
  if (!solveIKBest(xr, yr, th1, th2)) return false;

  setJoints(th1, th2);
  delay(STEP_DELAY_MS);

  curX = x; curY = y;
  return true;
}

bool flipBranchAtCurrentXY(){
  float xr = curX + ORIGIN_X;
  float yr = curY + ORIGIN_Y;

  float th1D, th2D, th1U, th2U;
  bool okD = ikSigned(xr, yr, +1.0f, th1D, th2D);
  bool okU = ikSigned(xr, yr, -1.0f, th1U, th2U);
  if (!(okD && okU)) return false;

  float dD = angleDist(th1D, curTh1) + angleDist(th2D, curTh2);
  float dU = angleDist(th1U, curTh1) + angleDist(th2U, curTh2);

  if (dD <= dU) setJoints(th1U, th2U);
  else          setJoints(th1D, th2D);

  delay(BRANCH_FLIP_DELAY_MS);
  return true;
}

bool moveToWithFlipRetry(float x, float y){
  if (moveTo(x, y)) return true;
  if (flipBranchAtCurrentXY()) {
    if (moveTo(x, y)) return true;
  }
  return false;
}

bool moveLineSmooth(float x1, float y1){
  float x0 = curX, y0 = curY;
  float dx = x1 - x0;
  float dy = y1 - y0;
  float dist = sqrtf(dx*dx + dy*dy);
  int steps = (int)ceilf(dist / LINE_STEP_MM);
  if (steps < 1) steps = 1;

  for (int i = 1; i <= steps; i++){
    float t = (float)i / (float)steps;
    float x = x0 + t * dx;
    float y = y0 + t * dy;
    if (!moveToWithFlipRetry(x, y)) return false;
  }
  return true;
}

bool reachableSoftware(float x, float y){
  float xr = x + ORIGIN_X;
  float yr = y + ORIGIN_Y;
  float th1, th2;
  return solveIKBest(xr, yr, th1, th2);
}

void homeAndSetOrigin(){
  sBase.write(applyServoMap((float)HOME_BASE_DEG,  INV_BASE,  OFFSET_BASE_DEG));
  sElbow.write(applyServoMap((float)HOME_ELBOW_DEG, INV_ELBOW, OFFSET_ELBOW_DEG));
  penUp();
  delay(900);

  curTh1 = deg2rad((float)HOME_BASE_DEG);
  curTh2 = deg2rad((float)HOME_ELBOW_DEG);

  float hx, hy;
  fk(curTh1, curTh2, hx, hy);
  ORIGIN_X = hx;
  ORIGIN_Y = hy;

  curX = 0; curY = 0;
}

// Make the CURRENT physical point become software (0,0)
void setSoftwareOriginHere(){
  float xr = curX + ORIGIN_X;
  float yr = curY + ORIGIN_Y;
  ORIGIN_X = xr;
  ORIGIN_Y = yr;
  curX = 0.0f;
  curY = 0.0f;
}

// Find left-bottom edge then move inward and set that as (0,0)
void calibratePaperCornerOrigin(){
  const float y = 0.0f;

  // start from old origin
  penUp();
  moveLineSmooth(0.0f, 0.0f);
  moveLineSmooth(curX, y);

  // scan left to edge
  while (true){
    float nextX = curX - SCAN_STEP_MM;
    if (!reachableSoftware(nextX, y)) {
      if (flipBranchAtCurrentXY() && reachableSoftware(nextX, y)) {
        moveLineSmooth(nextX, y);
        continue;
      }
      break;
    }
    if (!moveLineSmooth(nextX, y)) break;
  }

  // move inward onto paper
  moveLineSmooth(curX + INSET_X, 0.0f);
  moveLineSmooth(curX, INSET_Y);

  // redefine origin here
  setSoftwareOriginHere();
}

// Draw one quarter-circle in the +x,+y quadrant from the corner origin
bool drawQuarterCircle(){
  // Start point at angle 0: (R,0)
  penUp();
  if (!moveLineSmooth(R, 0.0f)) return false;

  penDown();
  for (int i = 1; i <= ARC_SEGMENTS; i++){
    float t = (float)i / (float)ARC_SEGMENTS;
    float deg = ARC_START_DEG + t * (ARC_END_DEG - ARC_START_DEG);
    float a = deg2rad(deg);

    float x = R * cosf(a);
    float y = R * sinf(a);

    if (!moveLineSmooth(x, y)) { penUp(); return false; }
  }
  penUp();
  return true;
}

void setup(){
  Serial.begin(115200);
  delay(200);

  sBase.setPeriodHertz(50);
  sElbow.setPeriodHertz(50);
  sPen.setPeriodHertz(50);

  sBase.attach(PIN_BASE, 500, 2400);
  sElbow.attach(PIN_ELBOW, 500, 2400);
  sPen.attach(PIN_PEN, 500, 2400);

  homeAndSetOrigin();
  calibratePaperCornerOrigin(); // now (0,0) is the paper corner (inset)
}

void loop(){
  // loop: keep drawing the same quarter-circle
  bool ok = drawQuarterCircle();
  if (!ok) {
    // if it fails, lift pen and re-calibrate corner (safe)
    penUp();
    calibratePaperCornerOrigin();
  }
  delay(300);
}
