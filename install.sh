#!/bin/bash
# =============================================================================
# install.sh  —  Installation et vérification des dépendances
# Projet Pratique 2 — Gestion Cybersécurité / Données Personnelles — UQAC
# =============================================================================

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  Installation — Sanitization or Deception? (PoPETs 2026)"
echo "══════════════════════════════════════════════════════════"
echo ""

# ── Python ──
echo "[1/4] Vérification de Python..."
if ! command -v python3 &>/dev/null; then
    echo "  ❌  Python 3 non trouvé. Installez Python 3.8+ depuis python.org"
    exit 1
fi
PYVER=$(python3 --version)
echo "  ✓  $PYVER"

# ── pip ──
echo "[2/4] Installation des dépendances Python..."
python3 -m pip install --upgrade pip -q
python3 -m pip install spacy matplotlib tabulate -q

if [ $? -eq 0 ]; then
    echo "  ✓  spacy, matplotlib, tabulate installés"
else
    echo "  ⚠️   Installation partielle — le script fonctionnera quand même en mode dégradé"
fi

# ── spaCy model ──
echo "[3/4] Téléchargement du modèle NER (en_core_web_sm)..."
python3 -m spacy download en_core_web_sm -q 2>/dev/null

if python3 -c "import spacy; spacy.load('en_core_web_sm')" &>/dev/null; then
    echo "  ✓  Modèle spaCy chargé avec succès"
else
    echo "  ⚠️   Modèle spaCy non disponible — mode regex activé (fonctionnel)"
fi

# ── Vérification fichiers ──
echo "[4/4] Vérification des fichiers du projet..."
FILES=("demo_live.py" "generate_graph.py"
       "sanitization_deception_slides.pptx" "README.md")
OK=1
for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
        echo "  ✓  $f"
    else
        echo "  ❌  $f  (manquant)"
        OK=0
    fi
done

echo ""
echo "══════════════════════════════════════════════════════════"
if [ $OK -eq 1 ]; then
    echo "  ✅  Installation complète ! Vous pouvez lancer :"
else
    echo "  ⚠️   Certains fichiers sont manquants."
fi
echo ""
echo "  Démo interactive (présentation en classe) :"
echo "    python3 demo_live.py --auto     # Démo automatique"
echo ""
echo "  Générer le graphique seul :"
echo "    python3 generate_graph.py"
echo "══════════════════════════════════════════════════════════"
echo ""
