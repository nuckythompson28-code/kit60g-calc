"""
KIT60G 갱타입 선반 - 소재길이별 생산개수 계산기
O0852 / O9001 / O9002 / O9003 로직 기반
"""
import math

# === 기본 파라미터 (코드에서 추출) ===
CHUCK_INIT = 75       # #103 초기 척 길이
SAFETY_LEN = 12       # #530 안전 길이
CHUCK_LEFT = 15       # #531 척 좌측 한계
CHUCK2JAW = 1.03      # #532 척~조 거리
FACE_CUT = 1          # #104 초기 페이스컷
MARGIN = 0.2          # #123 마진값
RESIDUAL = 15         # #129 잔재 안전값 (RS40 소재: 15, 일반: 0)

# === 제품 설정 ===
FIN_LEN = 8.0         # #113 완성 길이 (제품 폭)
TIP_WIDTH = 2.0       # #114 팁 폭 (파팅바이트 폭)
UNIT_WIDTH = FIN_LEN + TIP_WIDTH  # #505 = 10mm

DEAD_ZONE = CHUCK_LEFT + CHUCK2JAW + SAFETY_LEN  # 못 쓰는 구간

MAT_TYPE = "RS40" if RESIDUAL > 0 else "일반(CN/CM)"

print(f"=== KIT60G 생산개수 계산 ===")
print(f"소재 타입: {MAT_TYPE}  (잔재안전값 #129={RESIDUAL}mm)")
print(f"제품 단위폭(#505): {UNIT_WIDTH}mm (완성{FIN_LEN} + 팁{TIP_WIDTH})")
print(f"척 초기길이: {CHUCK_INIT}mm, 안전길이: {SAFETY_LEN}mm")
print()

# === 못 쓰는 구간 표시 ===
print(f"[못 쓰는 구간 (데드존)]")
print(f"  척 좌측 한계(#531):  {CHUCK_LEFT}mm")
print(f"  척~조 거리(#532):    {CHUCK2JAW}mm")
print(f"  안전 거리(#530):     {SAFETY_LEN}mm")
if RESIDUAL > 0:
    print(f"  잔재 안전값(#129):   {RESIDUAL}mm   ← RS40 강제 적용")
print(f"  ─────────────────────────")
print(f"  합계:                {DEAD_ZONE + RESIDUAL}mm  ← 소재 끝에서 이만큼 못 씀")
print(f"  + 페이스컷(#104):    {FACE_CUT}mm   ← 첫 가공 시 날림")
print(f"  + 마진(#123):        {MARGIN}mm   ← 오토링크마다 소모")
print(f"  + 마지막 팁폭(#114): {TIP_WIDTH}mm   ← 잔재 인출 시 소모")
print()

# === 척 최적화 (O9001 로직) ===
pcs_per_chuck = math.floor((CHUCK_INIT - SAFETY_LEN) / UNIT_WIDTH)  # #602
chuck_opt = pcs_per_chuck * UNIT_WIDTH + SAFETY_LEN                  # #103 재계산
eff_len = chuck_opt - SAFETY_LEN                                     # #500
pcs_per_cycle = math.floor(eff_len / UNIT_WIDTH)                     # #517
mach_len = pcs_per_cycle * UNIT_WIDTH                                # #518

print(f"[척 최적화]")
print(f"  척당 개수: {pcs_per_cycle}개")
print(f"  최적 척길이: {chuck_opt}mm (원래 {CHUCK_INIT}mm)")
print(f"  유효 가공길이: {eff_len}mm")
print(f"  실 가공길이: {mach_len}mm")
print()

# === #102=500 기준, #101 변화에 따른 상세 표 ===
print(f"{'='*90}")
print(f"  #102=500 고정, #101(0~99) 변화 시 생산개수")
print(f"{'='*90}")
print(f"{'#101 범위':^18} | {'소재길이':^12} | {'총개수':^6} | {'오토링크':^6} | {'잔재개수':^6} | {'버림길이':^8} | {'비고'}")
print(f"{'-'*90}")

prev_key = None
group_start_101 = None

for v101 in range(0, 100):
    mat_len = 500 + v101
    eff_mat = mat_len - RESIDUAL  # #140 = #101 + #102 - #129

    # 오토링크 횟수
    auto_pulls = math.floor(
        (eff_mat - CHUCK_LEFT - CHUCK2JAW - SAFETY_LEN - mach_len - TIP_WIDTH - FACE_CUT)
        / (mach_len + TIP_WIDTH + MARGIN)
    )
    if auto_pulls < 0:
        auto_pulls = 0

    pcs_main = pcs_per_cycle * (1 + auto_pulls)

    # 잔재 계산
    consumed = (mach_len + TIP_WIDTH + FACE_CUT) + auto_pulls * (mach_len + TIP_WIDTH + MARGIN)
    remain_raw = eff_mat - consumed - DEAD_ZONE - (TIP_WIDTH + MARGIN)
    remain_pcs = max(0, math.floor(remain_raw / UNIT_WIDTH))

    total = pcs_main + remain_pcs

    # 실제 버리는 길이 계산
    total_used = total * UNIT_WIDTH  # 제품으로 쓴 길이
    scrap = mat_len - total_used - DEAD_ZONE - FACE_CUT - (auto_pulls * MARGIN) - TIP_WIDTH - MARGIN
    if remain_pcs > 0:
        scrap = remain_raw - (remain_pcs * UNIT_WIDTH)

    key = (total, auto_pulls, remain_pcs)

    if key != prev_key:
        if group_start_101 is not None:
            note = ""
            if prev_remain == 0 and prev_auto > 0:
                note = "딱 맞음"
            elif prev_scrap < 2:
                note = "거의 꽉 참"
            print(f"  #101={group_start_101:2d}~{prev_101:2d}  "
                  f"| {500+group_start_101:3d}~{500+prev_101:3d}mm  "
                  f"|  {prev_total:3d}   "
                  f"|  {prev_auto:3d}   "
                  f"|  {prev_remain:3d}   "
                  f"| {prev_scrap:5.1f}mm  "
                  f"| {note}")
        group_start_101 = v101
        prev_key = key
    prev_101 = v101
    prev_total = total
    prev_auto = auto_pulls
    prev_remain = remain_pcs
    prev_scrap = scrap

# 마지막 그룹
if group_start_101 is not None:
    note = ""
    if prev_remain == 0 and prev_auto > 0:
        note = "딱 맞음"
    print(f"  #101={group_start_101:2d}~{prev_101:2d}  "
          f"| {500+group_start_101:3d}~{500+prev_101:3d}mm  "
          f"|  {prev_total:3d}   "
          f"|  {prev_auto:3d}   "
          f"|  {prev_remain:3d}   "
          f"| {prev_scrap:5.1f}mm  "
          f"| {note}")

print(f"{'='*90}")

# === 전체 범위 요약 (간략) ===
print(f"\n{'='*90}")
print(f"  전체 소재길이 범위별 생산개수 요약")
print(f"{'='*90}")
print(f"{'소재길이(mm)':^18} | {'총개수':^6} | {'오토링크':^6} | {'잔재':^4} | {'버림길이 범위':^16}")
print(f"{'-'*90}")

prev_total_g = -1
range_start = None

for mat_len_10 in range(900, 5810):
    mat_len = mat_len_10 / 10.0
    eff_mat = mat_len - RESIDUAL  # #140 = 소재길이 - #129

    if mat_len > 580:
        break
    if eff_mat <= chuck_opt:
        continue

    auto_pulls = math.floor(
        (eff_mat - CHUCK_LEFT - CHUCK2JAW - SAFETY_LEN - mach_len - TIP_WIDTH - FACE_CUT)
        / (mach_len + TIP_WIDTH + MARGIN)
    )
    if auto_pulls < 0:
        auto_pulls = 0

    pcs_main = pcs_per_cycle * (1 + auto_pulls)
    consumed = (mach_len + TIP_WIDTH + FACE_CUT) + auto_pulls * (mach_len + TIP_WIDTH + MARGIN)
    remain_raw = eff_mat - consumed - DEAD_ZONE - (TIP_WIDTH + MARGIN)
    remain_pcs = max(0, math.floor(remain_raw / UNIT_WIDTH))
    total = pcs_main + remain_pcs

    if remain_pcs > 0:
        scrap = remain_raw - (remain_pcs * UNIT_WIDTH)
    else:
        scrap = max(0, remain_raw)

    if total != prev_total_g:
        if range_start is not None:
            note = ""
            if prev_total_g % pcs_per_cycle == 0:
                note = f"← AL {prev_total_g // pcs_per_cycle - 1}회"
            print(f"  {range_start:6.1f}~{prev_len:6.1f}  "
                  f"|  {prev_total_g:3d}   "
                  f"|  {prev_auto_g:3d}   "
                  f"| {prev_rem_g:2d}  "
                  f"| {prev_scrap_min:4.1f}~{prev_scrap_max:4.1f}mm    "
                  f"  {note}")
        range_start = mat_len
        prev_total_g = total
        prev_auto_g = auto_pulls
        prev_rem_g = remain_pcs
        prev_scrap_min = scrap
        prev_scrap_max = scrap
    else:
        prev_scrap_min = min(prev_scrap_min, scrap)
        prev_scrap_max = max(prev_scrap_max, scrap)
    prev_len = mat_len

if range_start is not None:
    note = ""
    if prev_total_g % pcs_per_cycle == 0:
        note = f"← AL {prev_total_g // pcs_per_cycle - 1}회"
    print(f"  {range_start:6.1f}~{prev_len:6.1f}  "
          f"|  {prev_total_g:3d}   "
          f"|  {prev_auto_g:3d}   "
          f"| {prev_rem_g:2d}  "
          f"| {prev_scrap_min:4.1f}~{prev_scrap_max:4.1f}mm    "
          f"  {note}")

print(f"{'='*90}")
print(f"\n[데드존 구성]")
if RESIDUAL > 0:
    print(f"  소재 끝 ← {CHUCK_LEFT}(척한계) + {CHUCK2JAW}(척투조) + {SAFETY_LEN}(안전) + {RESIDUAL}(RS잔재) = {DEAD_ZONE + RESIDUAL}mm 못 씀")
else:
    print(f"  소재 끝 ← {CHUCK_LEFT}(척한계) + {CHUCK2JAW}(척투조) + {SAFETY_LEN}(안전) = {DEAD_ZONE}mm 못 씀")
print(f"  첫 가공: 페이스컷 {FACE_CUT}mm 추가 소모")
print(f"  오토링크마다: 마진 {MARGIN}mm + 팁폭 {TIP_WIDTH}mm 추가 소모")
print(f"\n※ 팁폭(#114)이나 완성길이(#113)가 다르면 결과 달라짐")
print(f"※ RS40 소재(#105=2)나 OD<30은 #129=15 적용되어 개수 줄어듦")
