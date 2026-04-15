"""
Génère les graphiques de résultats de la démo (version standalone).
Utilise les résultats précalculés pour éviter la dépendance à spaCy.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import numpy as np


DOMAINS = ["Médical", "Juridique", "Financier", "RH"]
STRATEGIES = ["Masquage [MASK]", "Pseudonymisation", "Remplacement générique"]
COLORS = ["#E63946", "#F4A261", "#0EA5E9"]

# Scores de risque résiduel par domaine et stratégie (%)
RISK_DATA = {
    "Masquage [MASK]":          [77.8, 66.7, 100.0, 50.0],
    "Pseudonymisation":         [66.7, 50.0,  50.0, 66.7],
    "Remplacement générique":   [55.6, 50.0,  37.5, 33.3],
}

fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor("#F8FAFC")


fig.suptitle(
    "Benchmark de robustesse post-sanitisation NER\n"
    "Paudel et al., « Sanitization or Deception? » — PoPETs 2026, Article #0009",
    fontsize=14, fontweight="bold", y=0.98, color="#0D1B2A"
)

# Graphique 1 : Barres groupées par domaine
ax1 = fig.add_subplot(2, 2, (1, 2))
ax1.set_facecolor("#FFFFFF")

x = np.arange(len(DOMAINS))
width = 0.25

for i, (strat, col) in enumerate(zip(STRATEGIES, COLORS)):
    vals = RISK_DATA[strat]
    offset = (i - 1) * width
    bars = ax1.bar(x + offset, vals, width, label=strat, color=col, alpha=0.88,
                   edgecolor="white", linewidth=0.8)
    for bar, v in zip(bars, vals):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.2,
            f"{v:.0f}%",
            ha="center", va="bottom", fontsize=9, fontweight="bold",
            color="#334155"
        )

ax1.axhline(50, color="#94A3B8", linestyle="--", linewidth=1, alpha=0.7, label="Seuil 50%")
ax1.set_xlabel("Domaine du texte", fontsize=11, color="#475569", labelpad=8)
ax1.set_ylabel("Taux de ré-identification (%)", fontsize=11, color="#475569")
ax1.set_title("Risque résiduel par domaine et stratégie de sanitisation",
              fontsize=12, color="#0D1B2A", fontweight="bold", pad=12)
ax1.set_xticks(x)
ax1.set_xticklabels(DOMAINS, fontsize=11)
ax1.set_ylim(0, 115)
ax1.yaxis.set_major_formatter(ticker.PercentFormatter())
ax1.spines[["top", "right"]].set_visible(False)
ax1.spines["left"].set_color("#CBD5E1")
ax1.spines["bottom"].set_color("#CBD5E1")
ax1.tick_params(colors="#64748B")
ax1.legend(fontsize=10, loc="upper right", framealpha=0.9)


ax1.axhspan(60, 115, alpha=0.04, color="#E63946")
ax1.axhspan(40, 60, alpha=0.04, color="#F4A261")
ax1.axhspan(0,  40, alpha=0.04, color="#0EA5E9")


for yp, label, col in [(85, "RISQUE ÉLEVÉ", "#E63946"),
                        (50, "RISQUE MOYEN", "#F4A261"),
                        (20, "RISQUE RÉDUIT", "#0EA5E9")]:
    ax1.text(3.42, yp, label, fontsize=7.5, color=col, alpha=0.6,
             ha="right", va="center", fontweight="bold")


# Graphique 2 : Boxplot distribution
ax2 = fig.add_subplot(2, 2, 3)
ax2.set_facecolor("#FFFFFF")

data_for_box = [RISK_DATA[s] for s in STRATEGIES]
bp = ax2.boxplot(
    data_for_box,
    patch_artist=True,
    medianprops={"color": "white", "linewidth": 2.5},
    whiskerprops={"linestyle": "--", "color": "#94A3B8"},
    capprops={"color": "#94A3B8"},
    flierprops={"marker": "o", "markersize": 5, "markerfacecolor": "#94A3B8"},
    notch=False,
    widths=0.5,
)
for patch, col in zip(bp["boxes"], COLORS):
    patch.set_facecolor(col)
    patch.set_alpha(0.85)
    patch.set_edgecolor("white")


for i, (strat, col) in enumerate(zip(STRATEGIES, COLORS)):
    y_vals = RISK_DATA[strat]
    x_vals = np.random.normal(i + 1, 0.07, size=len(y_vals))
    ax2.scatter(x_vals, y_vals, color="white", s=45, zorder=5,
                edgecolor=col, linewidth=1.5)

ax2.axhline(50, color="#94A3B8", linestyle="--", linewidth=1, alpha=0.7)
ax2.set_xticks(range(1, len(STRATEGIES) + 1))
ax2.set_xticklabels([s.replace(" ", "\n") for s in STRATEGIES], fontsize=9)
ax2.set_ylabel("Taux de ré-identification (%)", fontsize=10, color="#475569")
ax2.set_title("Distribution du risque\n(tous domaines)", fontsize=11,
              color="#0D1B2A", fontweight="bold")
ax2.set_ylim(0, 115)
ax2.yaxis.set_major_formatter(ticker.PercentFormatter())
ax2.spines[["top", "right"]].set_visible(False)
ax2.spines["left"].set_color("#CBD5E1")
ax2.spines["bottom"].set_color("#CBD5E1")
ax2.tick_params(colors="#64748B")


for i, strat in enumerate(STRATEGIES):
    avg = np.mean(RISK_DATA[strat])
    ax2.text(i + 1, avg + 4, f"moy.\n{avg:.0f}%", ha="center", va="bottom",
             fontsize=9, fontweight="bold", color=COLORS[i])


# Graphique 3 : Barres horizontales — moyennes

ax3 = fig.add_subplot(2, 2, 4)
ax3.set_facecolor("#FFFFFF")

avgs = [np.mean(RISK_DATA[s]) for s in STRATEGIES]
verdicts = ["[X] Insuffisant", "[!] Partiel", "[OK] Meilleur compromis"]
strat_short = ["Masquage\n[MASK]", "Pseudo-\nnymisation", "Remplacement\ngénérique"]

bars_h = ax3.barh(strat_short, avgs, color=COLORS, alpha=0.88, height=0.5,
                  edgecolor="white", linewidth=0.8)

for bar, avg, verdict, col in zip(bars_h, avgs, verdicts, COLORS):
    ax3.text(avg + 1, bar.get_y() + bar.get_height() / 2,
             f" {avg:.1f}%  {verdict}",
             va="center", fontsize=10, color="#334155", fontweight="bold")

ax3.axvline(50, color="#94A3B8", linestyle="--", linewidth=1, alpha=0.7)
ax3.set_xlim(0, 125)
ax3.set_xlabel("Risque moyen (%)", fontsize=10, color="#475569")
ax3.set_title("Risque moyen global\npar stratégie", fontsize=11,
              color="#0D1B2A", fontweight="bold")
ax3.xaxis.set_major_formatter(ticker.PercentFormatter())
ax3.spines[["top", "right"]].set_visible(False)
ax3.spines["left"].set_color("#CBD5E1")
ax3.spines["bottom"].set_color("#CBD5E1")
ax3.tick_params(colors="#64748B")


fig.text(
    0.5, 0.005,
    "Proof of concept — Projet Pratique 2  ·  Gestion Cybersécurité/Données Personnelles  ·  UQAC  ·  Avril 2026",
    ha="center", fontsize=9, color="#94A3B8", style="italic"
)

plt.tight_layout(rect=[0, 0.02, 1, 0.95])
plt.savefig("/Users/ayat/Downloads/files (1)/risk_comparison.png", dpi=160, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print(" Graphique sauvegardé → risk_comparison.png")
plt.close()
