#!/usr/bin/env python3
"""Build phased corpus queues: 10% pilot then 60% scale."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 10% pilot — diverse, likely viable (full cycle validation)
PHASE1_SLUGS = [
    "soulful_lines",  # validated benchmark
    "whispering_souls",
    "cozy_oni",
    "uck_jep_r7_jm_s36taj_d34_gp4_va",
    "my_mind_garden",
]

# 60% scale — phase1 + additional slugs from main queue (priority order)
PHASE2_EXTRA_SLUGS = [
    "deep_verse",
    "lofi_tokyo",
    "lofi_geisha",
    "uccr5eci_ejimv_x2o1ti_youkq",
    "uc6z7_uni_fj1_y_0f_j51_z0va_w",
    "uccib_s8grf_u_rh0bec5g_td5_q",
    "ucj_d2yhx7_itf_hib8_imi_dfa_pw",
    "uck_e6_zz_ux_uy_xmp688ib_rwa",
    "ucb95x_csst23_wc2_fj3_bqqmg_a",
    "uc8_p3sr_ce55m_kq5_pbjq_i_mj_q",
    "ucg_oa9_fhqui8yfe_htw_w7g4n_q",
    "uc0u_gc_ebw_axw3ljqe_gjy2qw",
    "uc6gw68_ouc_jvjkbr_iivk_yvsw",
    "ucbn_hzuk_oqg73h7g_wi_iu0_ita",
    "uc2_fr_ph_vnvd_eegu4_ijedigd_q",
    "ucm3_uzg_ap4d_tj_fh_wf2_wcvu_aa",
    "ucebaodh_sar04x_1_vhh6h2_ig",
    "uc8_rz_a51ax_a_t_ar2_alu_ee_ama",
    "uc5s_ztr_l_olt_t_c_ogb_rxao_hw",
    "ucb_lkk_o7_d8_pwpqumq3xhd_jq",
    "ucdtx_f3_z_6gu_jw_bcu144n_gva",
    "uca9_pve_qrjn_xn4_ez_mxt_t4_qrg",
    "uc3p_ifz_qb_oll0_tn_edh1_uu5_gw",
    "ucgs_hlik_wm8af_josnh_nks2_sq",
    "ucyne_mzcnsf_zd6e_dbd6bzkt_q",
    "uc0o_wqx_m0i_lsy7_ne_znf_mpucw",
]


def _flatten_queue(data: dict) -> dict[str, dict]:
    by_slug: dict[str, dict] = {}
    for niche, items in (data.get("queue") or {}).items():
        for item in items or []:
            slug = item.get("slug")
            if slug:
                by_slug[slug] = {**item, "niche": niche}
    return by_slug


def _build_subset(data: dict, slugs: list[str]) -> dict:
    by_slug = _flatten_queue(data)
    buckets: dict[str, list] = {}
    for slug in slugs:
        if slug not in by_slug:
            continue
        entry = {k: v for k, v in by_slug[slug].items() if k != "niche"}
        entry.pop("status", None)  # always run in phased sprint
        niche = by_slug[slug]["niche"]
        buckets.setdefault(niche, []).append(entry)
    out = {
        "pipeline": data.get("pipeline", {}),
        "phase": data.get("phase", ""),
        "parent_queue": "corpus_queue.yaml",
        "queue": buckets,
    }
    return out


def main() -> int:
    src = PROJECT_ROOT / "corpus_queue.yaml"
    data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    total = sum(len(v) for v in data.get("queue", {}).values())

    phase1_slugs = PHASE1_SLUGS
    phase2_slugs = PHASE1_SLUGS + PHASE2_EXTRA_SLUGS
    # Cap phase2 at 60% of full queue
    cap = max(1, int(round(total * 0.60)))
    if len(phase2_slugs) > cap:
        phase2_slugs = phase2_slugs[:cap]

    p1 = _build_subset(data, phase1_slugs)
    p1["phase"] = f"pilot_10pct ({len(phase1_slugs)} of {total} channels)"

    p2 = _build_subset(data, phase2_slugs)
    p2["phase"] = f"scale_60pct ({len(phase2_slugs)} of {total} channels)"

    (PROJECT_ROOT / "corpus_queue_phase1.yaml").write_text(
        yaml.dump(p1, sort_keys=False, default_flow_style=False), encoding="utf-8"
    )
    (PROJECT_ROOT / "corpus_queue_phase2.yaml").write_text(
        yaml.dump(p2, sort_keys=False, default_flow_style=False), encoding="utf-8"
    )

    print(f"Full queue: {total} channels")
    print(f"Phase 1 (10%): {len(phase1_slugs)} -> corpus_queue_phase1.yaml")
    print(f"Phase 2 (60%): {len(phase2_slugs)} -> corpus_queue_phase2.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
