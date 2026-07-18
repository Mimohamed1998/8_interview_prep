"""Self-audit: assert every number quoted in chapter_4 draft against outputs/*.csv."""
import pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "outputs"
checks = []

def ck(name, actual, expected, nd=3):
    ok = round(float(actual), nd) == expected
    checks.append((name, ok, round(float(actual), nd), expected))

# ---- Table 4.1 descriptives
d = pd.read_csv(OUT / "descriptive_statistics.csv").set_index("variable")
exp = {
 "ERI": (0.620, 0.171, 0.339, 0.967, 0.624, 0.190, -0.582),
 "DIVP": (0.740, 0.042, 0.645, 0.800, 0.755, -0.675, -0.338),
 "DIVM": (0.793, 0.031, 0.695, 0.830, 0.799, -1.339, 1.828),
 "INF": (10.022, 8.619, -0.429, 49.721, 7.675, 3.085, 12.974),
 "EXR": (121.243, 74.166, 40.063, 327.507, 108.334, 1.548, 2.332),
 "log(FDI)": (19.699, 0.950, 17.585, 21.202, 19.889, -0.585, -0.399),
}
for v, (m, s, mn, mx, md, sk, ku) in exp.items():
    r = d.loc[v]
    for col, e in zip(["mean","std_dev","min","max","median","skewness","excess_kurtosis"],
                      [m, s, mn, mx, md, sk, ku]):
        ck(f"desc {v} {col}", r[col], e)
r = d.loc["FDI (raw)"]
ck("FDI mean", r["mean"], 513069259.226)
ck("FDI sd", r["std_dev"], 389463117.370)
ck("FDI min", r["min"], 43355119.720)
ck("FDI max", r["max"], 1614044009.000)
ck("FDI med", r["median"], 434075668.500)
ck("FDI skew", r["skewness"], 0.892)
ck("FDI kurt", r["excess_kurtosis"], 0.499)

c = pd.read_csv(OUT / "correlation_eri_divp_divm.csv", index_col=0)
ck("corr eri-divp", c.loc["eri","divp"], 0.364)
ck("corr eri-divm", c.loc["eri","divm"], 0.189)
ck("corr divp-divm", c.loc["divp","divm"], 0.534)
rc = pd.read_csv(OUT / "regressor_correlation_matrix.csv", index_col=0)
ck("corr exr-logfdi", rc.loc["EXR","log(FDI)"], 0.65, 2)
ck("corr divp-divm(reg)", rc.loc["DIVP","DIVM"], 0.53, 2)

# ---- ADF
a = pd.read_csv(OUT / "adf_stationarity_results.csv")
def adf(var, order, test_substr):
    m = a[(a.variable==var) & (a.order_tested==order) & a.test.str.contains(test_substr, regex=False)]
    assert len(m)>=1, (var, order, test_substr)
    return m.iloc[0]
for name, row, stat, p, crit in [
    ("ERI lvl", adf("ERI","level","uncapped"), -3.234, 0.018, -2.951),
    ("INF lvl", adf("INF","level","uncapped"), -4.881, None, -2.951),
    ("DIVP lvl", adf("DIVP","level","uncapped"), -1.338, 0.612, -2.951),
    ("DIVP d1", adf("DIVP","1st difference","uncapped"), -4.626, None, -2.954),
    ("DIVM lvl", adf("DIVM","level","uncapped"), -2.589, 0.095, -2.951),
    ("DIVM d1", adf("DIVM","1st difference","uncapped"), -6.552, None, -2.954),
    ("logFDI lvl", adf("log(FDI)","level","uncapped"), -1.968, 0.619, -3.558),
    ("logFDI d1", adf("log(FDI)","1st difference","uncapped"), -7.650, None, -2.957),
    ("EXR lvl unc", adf("EXR","level","uncapped"), -1.111, 0.927, -3.612),
    ("EXR lvl cap", adf("EXR","level","maxlag=4"), 2.866, 1.000, -3.558),
    ("EXR lvl pp", adf("EXR","level","Phillips"), -1.064, 0.935, None),
    ("EXR d1 unc", adf("EXR","1st difference","uncapped"), 0.218, 0.973, -2.998),
    ("EXR d1 cap", adf("EXR","1st difference","maxlag=4"), 1.294, 0.997, -2.961),
    ("EXR d1 pp", adf("EXR","1st difference","Phillips"), -5.054, None, -2.954),
    ("EXR d2", adf("EXR","2nd difference","uncapped"), 0.686, 0.990, -2.998),
]:
    ck(f"ADF {name} stat", row["stat"], stat)
    if p is not None: ck(f"ADF {name} p", row["p_value"], p)
    if crit is not None: ck(f"ADF {name} crit5", row["crit_5pct"], crit)

# ---- VIF
v = pd.read_csv(OUT / "vif_results.csv").set_index("regressor")
for reg, e in [("EXR",2.190),("log(FDI)",2.186),("DIVM",1.868),("DIVP",1.535),("SHOCK",1.416),("INF",1.329)]:
    ck(f"VIF {reg}", v.loc[reg,"vif"], e)

# ---- Model A
ma = pd.read_csv(OUT / "model_a_static_ols_coefficients.csv").set_index("term")
mah = pd.read_csv(OUT / "model_a_hac_coefficients.csv").set_index("term")
for t, co, se, ts, p, seh, th, ph, nd in [
    ("const",-2.334,0.731,-3.196,0.003,0.737,-3.167,0.004,3),
    ("DIVP",1.268,0.602,2.105,0.044,0.574,2.209,0.036,3),
    ("DIVM",-0.805,0.888,-0.907,0.372,0.636,-1.266,0.216,3),
    ("EXR",-0.000941,0.000408,-2.308,0.029,0.000467,-2.017,0.053,6),
    ("log(FDI)",0.143,0.032,4.488,None,0.032,4.406,None,3),
    ("SHOCK",-0.020,0.069,-0.297,0.769,0.045,-0.457,0.651,3),
]:
    ck(f"A {t} coef", ma.loc[t,"coef"], co, nd)
    ck(f"A {t} se", ma.loc[t,"std_err"], se, nd)
    ck(f"A {t} t", ma.loc[t,"t_stat"], ts)
    if p is not None: ck(f"A {t} p", ma.loc[t,"p_value"], p)
    ck(f"A {t} seh", mah.loc[t,"std_err_hac"], seh, nd)
    ck(f"A {t} th", mah.loc[t,"t_stat_hac"], th)
    if ph is not None: ck(f"A {t} ph", mah.loc[t,"p_value_hac"], ph)
ck("A INF coef", ma.loc["INF","coef"], -0.004062, 6)
ck("A INF se", ma.loc["INF","std_err"], 0.002733, 6)
ck("A INF t", ma.loc["INF","t_stat"], -1.486)
ck("A INF p", ma.loc["INF","p_value"], 0.148)
ck("A INF seh", mah.loc["INF","std_err_hac"], 0.002989, 6)
ck("A INF th", mah.loc["INF","t_stat_hac"], -1.359)
ck("A INF ph", mah.loc["INF","p_value_hac"], 0.185)
fa = pd.read_csv(OUT / "model_a_static_ols_fit_stats.csv").iloc[0]
ck("A R2", fa.r_squared, 0.598); ck("A adjR2", fa.adj_r_squared, 0.512)
ck("A F", fa.f_statistic, 6.953); ck("A AIC", fa.aic, -43.377); ck("A BIC", fa.bic, -32.489)
assert fa.n_obs == 35

# ---- lag grid
lg = pd.read_csv(OUT / "ardl_lag_selection.csv").set_index(["p","q"])
ck("lag11 aic", lg.loc[(1,1),"aic"], -32.306); ck("lag11 bic", lg.loc[(1,1),"bic"], -9.858)
ck("lag12 aic", lg.loc[(1,2),"aic"], -40.295); ck("lag12 bic", lg.loc[(1,2),"bic"], -8.868)
ck("lag21 aic", lg.loc[(2,1),"aic"], -35.152); ck("lag21 bic", lg.loc[(2,1),"bic"], -11.208)
ck("lag22 aic", lg.loc[(2,2),"aic"], -39.796); ck("lag22 bic", lg.loc[(2,2),"bic"], -6.872)
assert (lg.loc[(1,1),"k_params"], lg.loc[(1,2),"k_params"], lg.loc[(2,1),"k_params"], lg.loc[(2,2),"k_params"]) == (14,20,15,21)
# grid (common 33-obs sample): 19 vs 13; final N=34 fits: 20 vs 14 (model_comparison_side_by_side.csv)
assert lg.loc[(1,2),"df_resid"] == 13 and lg.loc[(1,1),"df_resid"] == 19
mc = pd.read_csv(OUT / "model_comparison_side_by_side.csv").set_index("regressor")
assert mc.loc["df_resid","ardl_long_run_capped_(1,1)"] == "20"
assert mc.loc["df_resid","ardl_long_run_grid_(1,2)"] == "14"

# ---- bounds
b = pd.read_csv(OUT / "ardl_bounds_test.csv")
bc = pd.read_csv(OUT / "ardl_capped_1_1_bounds_test.csv")
ck("F grid", b.f_stat.iloc[0], 2.823); ck("F capped", bc.f_stat.iloc[0], 2.366)
for lvl, lo, hi in [(90.0,2.031,3.136),(95.0,2.328,3.500),(99.0,2.957,4.252)]:
    r = b[b.confidence_level_pct==lvl].iloc[0]
    ck(f"bounds {lvl} lo", r.crit_lower, lo); ck(f"bounds {lvl} hi", r.crit_upper, hi)

# ---- ARDL LR / ECT / SR
lr = pd.read_csv(OUT / "ardl_capped_1_1_long_run_coefficients.csv").set_index("term")
lrh = pd.read_csv(OUT / "ardl_capped_1_1_long_run_hac_comparison.csv")
lrh.index = [t.replace(".L1","") for t in lrh.term]
for t, co, se, ts, p, seh, ph, nd in [
    ("const",1.678,1.329,1.262,0.207,0.847,0.061,3),
    ("DIVP",-1.045,0.983,-1.063,0.288,0.676,0.138,3),
    ("DIVM",1.205,1.680,0.718,0.473,0.692,0.097,3),
    ("INF",0.002154,0.007343,0.293,0.769,0.006026,0.724,6),
    ("EXR",0.000055,0.000890,0.062,0.951,0.000663,0.935,6),
    ("log(FDI)",-0.130,0.059,-2.191,0.028,0.038,0.003,3),
    ("SHOCK",0.023,0.131,0.175,0.861,0.072,0.753,3),
]:
    ck(f"LR {t} coef", lr.loc[t,"long_run_coef"], co, nd)
    ck(f"LR {t} se", lr.loc[t,"std_err_delta_method"], se, nd)
    ck(f"LR {t} t", lr.loc[t,"t_stat"], ts)
    ck(f"LR {t} p", lr.loc[t,"p_value"], p)
    ck(f"LR {t} seh", lrh.loc[t,"std_err_hac"], seh, nd)
    ck(f"LR {t} ph", lrh.loc[t,"p_value_hac"], ph)
ect = pd.read_csv(OUT / "ardl_capped_1_1_error_correction_term.csv").iloc[0]
ck("ECT coef", ect.coef, -0.759); ck("ECT se", ect.std_err, 0.238)
ck("ECT t", ect.t_stat, -3.190); ck("ECT p", ect.p_value, 0.005)
e2 = pd.read_csv(OUT / "ardl_error_correction_term.csv").iloc[0]
ck("ECT12 coef", e2.coef, -1.006); ck("ECT12 se", e2.std_err, 0.271)
ck("ECT12 t", e2.t_stat, -3.718); ck("ECT12 p", e2.p_value, 0.002)
sr = pd.read_csv(OUT / "ardl_capped_1_1_short_run_coefficients.csv").set_index("term")
for t, co, se, ts, p, nd in [
    ("D.DIVP.L0",1.375,1.610,0.854,0.403,3), ("D.DIVM.L0",-0.949,1.170,-0.811,0.427,3),
    ("D.INF.L0",0.003660,0.006638,0.551,0.587,6), ("D.EXR.L0",-0.004547,0.002730,-1.665,0.111,6),
    ("D.log(FDI).L0",0.116,0.058,1.980,0.062,3), ("D.SHOCK.L0",-0.013,0.086,-0.150,0.882,3),
]:
    ck(f"SR {t} coef", sr.loc[t,"coef"], co, nd); ck(f"SR {t} se", sr.loc[t,"std_err"], se, nd)
    ck(f"SR {t} t", sr.loc[t,"t_stat"], ts); ck(f"SR {t} p", sr.loc[t,"p_value"], p)

# ---- primary diff OLS
md_ = pd.read_csv(OUT / "model_b_first_differenced_ols_coefficients.csv").set_index("term")
mdh = pd.read_csv(OUT / "model_diff_hac_coefficients.csv").set_index("term")
for t, co, se, ts, p, seh, th, ph, nd in [
    ("const",0.031,0.030,1.023,0.316,0.018,1.670,0.106,3),
    ("DIVP",2.353,1.379,1.706,0.100,1.185,1.986,0.057,3),
    ("DIVM",-1.402,1.044,-1.343,0.190,0.802,-1.750,0.092,3),
    ("INF",0.000152,0.003758,0.040,0.968,0.002605,0.058,0.954,6),
    ("EXR",-0.003543,0.001800,-1.968,0.059,0.000972,-3.646,0.001,6),
    ("log(FDI)",0.117,0.053,2.193,0.037,0.045,2.626,0.014,3),
    ("SHOCK",-0.010,0.086,-0.122,0.904,0.069,-0.152,0.880,3),
]:
    ck(f"P {t} coef", md_.loc[t,"coef"], co, nd); ck(f"P {t} se", md_.loc[t,"std_err"], se, nd)
    ck(f"P {t} t", md_.loc[t,"t_stat"], ts); ck(f"P {t} p", md_.loc[t,"p_value"], p)
    ck(f"P {t} seh", mdh.loc[t,"std_err_hac"], seh, nd)
    ck(f"P {t} th", mdh.loc[t,"t_stat_hac"], th); ck(f"P {t} ph", mdh.loc[t,"p_value_hac"], ph)
fd = pd.read_csv(OUT / "model_b_first_differenced_ols_fit_stats.csv").iloc[0]
ck("P R2", fd.r_squared, 0.423); ck("P adjR2", fd.adj_r_squared, 0.295)
ck("P F", fd.f_statistic, 3.300); ck("P pF", fd.f_pvalue, 0.014)
ck("P AIC", fd.aic, -30.219); ck("P BIC", fd.bic, -19.535)
assert fd.n_obs == 34

# ---- diagnostics
da = pd.read_csv(OUT / "diagnostics_model_a_ols.csv")
ck("dA DW", da.iloc[0].statistic, 1.557); ck("dA BP", da.iloc[1].statistic, 3.650)
ck("dA BP p", da.iloc[1].p_value, 0.724); ck("dA JB", da.iloc[2].statistic, 0.619)
ck("dA JB p", da.iloc[2].p_value, 0.734); ck("dA RESET", da.iloc[3].statistic, 0.011)
ck("dA RESET p", da.iloc[3].p_value, 0.989)
dd = pd.read_csv(OUT / "diagnostics_model_diff_ols.csv")
ck("dP DW", dd.iloc[0].statistic, 2.381); ck("dP BP", dd.iloc[1].statistic, 2.150)
ck("dP BP p", dd.iloc[1].p_value, 0.905); ck("dP JB", dd.iloc[2].statistic, 0.257)
ck("dP JB p", dd.iloc[2].p_value, 0.879); ck("dP RESET", dd.iloc[3].statistic, 1.636)
ck("dP RESET p", dd.iloc[3].p_value, 0.215)
db = pd.read_csv(OUT / "diagnostics_model_b_ardl_capped.csv")
ck("dB BG1", db.iloc[0].statistic, 3.319); ck("dB BG1 p", db.iloc[0].p_value, 0.068)
ck("dB BG2", db.iloc[1].statistic, 6.841); ck("dB BG2 p", db.iloc[1].p_value, 0.033)
ck("dB BP", db.iloc[2].statistic, 12.764); ck("dB BP p", db.iloc[2].p_value, 0.466)
ck("dB JB", db.iloc[3].statistic, 0.337); ck("dB JB p", db.iloc[3].p_value, 0.845)
ck("dB RESET", db.iloc[4].statistic, 1.682); ck("dB RESET p", db.iloc[4].p_value, 0.214)

# ---- robustness
rb = pd.read_csv(OUT / "robustness_checks_comparison.csv")
rows = {r.check.split(" ")[0] + r.check.split(" ")[1] if r.check.startswith("Check") else "Baseline": r
        for _, r in rb.iterrows()}
def rrow(sub): return rb[rb.check.str.contains(sub, regex=False)].iloc[0]
for sub, dp, dpo, dph, dm, dmo, dmh in [
    ("Baseline", 2.353, 0.100, 0.057, -1.402, 0.190, 0.092),
    ("Check 1", 2.086, 0.111, 0.069, -0.974, 0.325, 0.153),
    ("Check 2", 2.109, 0.122, 0.072, -0.129, 0.898, 0.795),
    ("Check 3", 1.518, 0.278, 0.145, -0.964, 0.367, 0.140),
]:
    r = rrow(sub)
    ck(f"rob {sub} divp", r.divp_coef, dp); ck(f"rob {sub} divp p", r.divp_p_original, dpo)
    ck(f"rob {sub} divp ph", r.divp_p_hac, dph); ck(f"rob {sub} divm", r.divm_coef, dm)
    ck(f"rob {sub} divm p", r.divm_p_original, dmo); ck(f"rob {sub} divm ph", r.divm_p_hac, dmh)
f1 = pd.read_csv(OUT / "robustness_check1_1990_2023_fit_stats.csv").iloc[0]
f2 = pd.read_csv(OUT / "robustness_check2_excl_shock_fit_stats.csv").iloc[0]
f3 = pd.read_csv(OUT / "robustness_check3_raw_fdi_fit_stats.csv").iloc[0]
ck("rob1 R2", f1.r_squared, 0.392); ck("rob2 R2", f2.r_squared, 0.451); ck("rob3 R2", f3.r_squared, 0.423)
assert (f1.n_obs, f2.n_obs, f3.n_obs) == (33, 29, 34)
c2 = pd.read_csv(OUT / "robustness_check2_excl_shock_coefficients.csv").set_index("term")
ck("rob2 INF", c2.loc["INF","coef"], -0.012); ck("rob2 INF p", c2.loc["INF","p_value"], 0.029)
c3 = pd.read_csv(OUT / "robustness_check3_raw_fdi_coefficients.csv").set_index("term")
ck("rob3 FDI p", c3.loc["FDI","p_value"], 0.037)

# ---- derived claims
ck("0.1*DIVP", 2.3529278361384054*0.1, 0.235)
ck("0.1*DIVM", 1.4023679591902016*0.1, 0.140)
ck("ERI range", 0.9667-0.3391, 0.628)
ck("SDs", 0.23529/0.1706780148592739, 1.4, 1)
ck("check1 shift", 2.0857529402077186-2.3529278361384054, -0.267)
ck("ECT pct", 75.9, 75.9, 1)

# ---- trend facts
f = pd.read_csv(OUT / "analysis_frame_1990_2024.csv")
assert (f.divm > f.divp).sum() == 32
assert set(f[f.divm <= f.divp].year) == {1994, 1995, 2024}
g = f.set_index("year")
for y, e in [(2008,0.898),(2009,0.562),(2020,0.414),(2022,0.357),(2023,0.415),(2024,0.895),(2011,0.967),(1992,0.339)]:
    ck(f"eri {y}", g.loc[y,"eri"], e)
ck("divp 1990", g.loc[1990,"divp"], 0.794); ck("divp 2000", g.loc[2000,"divp"], 0.645)
ck("divp 2024", g.loc[2024,"divp"], 0.800); ck("divm 1990", g.loc[1990,"divm"], 0.830)
ck("divm 1995", g.loc[1995,"divm"], 0.695); ck("divm 2020", g.loc[2020,"divm"], 0.829)
ck("divm 2024", g.loc[2024,"divm"], 0.792)

fails = [c for c in checks if not c[1]]
print(f"{len(checks)} checks, {len(fails)} failures")
for name, _, got, expct in fails:
    print(f"  FAIL {name}: file has {got}, draft says {expct}")
