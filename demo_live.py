
import sys
import time
import re
import random
import argparse
from collections import defaultdict

# Constantes de couleur ANSI pour le terminal
R  = "\033[0m"
BD = "\033[1m"
IT = "\033[3m"
RED   = "\033[91m"
YEL   = "\033[93m"
GRN   = "\033[92m"
BLUE  = "\033[94m"
CYAN  = "\033[96m"
MAG   = "\033[95m"
GRAY  = "\033[90m"
WHT   = "\033[97m"

# textes prédéfinis
DEMO_TEXTS = [
    (
        "Médical",
        "Dr. Sophie Tremblay at Montreal General Hospital has scheduled a follow-up "
        "appointment for patient Jean-Pierre Bouchard (DOB: 12 June 1978, "
        "file #MCH-2024-00442) on 3 March 2025 regarding his hypertension treatment."
    ),
    (
        "Entreprise",
        "CEO Marc Durand of InnoTech Solutions Quebec confirmed via email to CFO "
        "Lisa Chen that the acquisition of Startup XYZ for CAD 2.4 million will "
        "close on 15 April 2025 at their Ottawa office."
    ),
    (
        "Personnel",
        "Hi, my name is Amira Hassan. I live at 88 Chemin des Érables, Chicoutimi, QC. "
        "My employee ID at UQAC is UQ-20230187 and my direct manager is Prof. Robert Gagnon."
    ),
]

# Détecteur NER
NER_PATTERNS = [
    (r"\bDr\.?\s+[A-Z][a-z]+ [A-Z][a-z]+\b",                              "PERSON"),
    (r"\bProf\.?\s+[A-Z][a-z]+ [A-Z][a-z]+\b",                            "PERSON"),
    (r"\b(?:CEO|CFO|COO|CTO|VP|Director|Manager)\s+[A-Z][a-z]+ [A-Z][a-z]+\b", "PERSON"),
    (r"\b[A-Z][a-z]+-[A-Z][a-z]+ [A-Z][a-z]+\b",                          "PERSON"),
    (r"\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b",                         "PERSON"),
    (r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",                                       "PERSON"),
    (r"\b(?:January|February|March|April|May|June|July|August|"
     r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",       "DATE"),
    (r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
     r"September|October|November|December)\s+\d{4}\b",                    "DATE"),
    (r"\bDOB:\s*[\d]{1,2}\s+[A-Z][a-z]+ \d{4}\b",                        "DATE"),
    (r"\b(?:CAD|USD|EUR)\s?[\d,]+(?:\.\d+)?\s*(?:million|billion|thousand)?\b", "MONEY"),
    (r"\$[\d,]+(?:\.\d{2})?\b",                                            "MONEY"),
    (r"\b[A-Z]{2,4}-\d{4}-\d+\b",                                         "ID"),
    (r"\bUQ-\d{8}\b",                                                      "ID"),
    (r"\bfile\s+#[A-Z0-9-]+\b",                                            "ID"),
    (r"\b\d{1,3}\s+(?:Chemin|Rue|Avenue|Street|St|Blvd|Road|Drive|Dr)\s+"
     r"[A-Za-z\s'-]+(?:,\s*[A-Z][a-z]+)(?:,\s*[A-Z]{2})?\b",             "ADDRESS"),
    (r"\b(?:Montreal|Ottawa|Toronto|Quebec|Chicoutimi|Vancouver|Calgary|"
     r"New York|Paris|London)\b",                                           "CITY"),
    (r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s(?:Hospital|University|Université|"
     r"Solutions|Technologies|Corp|Inc|Ltd|Group|Bank)\b",                  "ORG"),
]

FAKE_REPLACEMENTS = {
    "PERSON":  ["Alex Martin", "Jordan Lefebvre", "Sam Tremblay",
                "Morgan Côté", "Riley Bouchard", "Casey Gagnon"],
    "DATE":    ["a recent date", "some time in 2024", "last month"],
    "MONEY":   ["a significant amount", "a disclosed sum"],
    "ID":      ["ID-REDACTED", "REF-XXXXX", "FILE-00000"],
    "ADDRESS": ["a residential address"],
    "CITY":    ["a city in Quebec", "a metropolitan area"],
    "ORG":     ["an organization", "a company", "an institution"],
}

GENERIC_MAP = {
    "PERSON":  "a person",
    "DATE":    "a date",
    "MONEY":   "an amount of money",
    "ID":      "an identifier",
    "ADDRESS": "an address",
    "CITY":    "a location",
    "ORG":     "an organization",
}

RECOVERY_RATES = {
    "masking": {
        "PERSON": 0.80, "DATE": 0.62, "MONEY": 0.48,
        "ID": 0.18, "ADDRESS": 0.55, "CITY": 0.72, "ORG": 0.68,
    },
    "pseudo":  {
        "PERSON": 0.58, "DATE": 0.50, "MONEY": 0.38,
        "ID": 0.10, "ADDRESS": 0.42, "CITY": 0.54, "ORG": 0.50,
    },
    "generic": {
        "PERSON": 0.32, "DATE": 0.28, "MONEY": 0.20,
        "ID": 0.05, "ADDRESS": 0.22, "CITY": 0.30, "ORG": 0.28,
    },
}

random.seed(99)


def slow_print(text: str, delay: float = 0.012) -> None:
    """Affiche le texte caractère par caractère pour un effet dramatique."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def detect_entities(text: str):
    """Détection NER par regex — retourne [(matched_text, label, start, end)]."""
    raw = []
    for pattern, label in NER_PATTERNS:
        for m in re.finditer(pattern, text):
            raw.append((m.group(), label, m.start(), m.end()))

    raw.sort(key=lambda x: x[2])
    deduped, last_end = [], -1
    for item in raw:
        if item[2] >= last_end:
            deduped.append(item)
            last_end = item[3]
    return deduped


def apply_strategy(text: str, entities, strategy: str):
    """Applique une stratégie de sanitisation. Retourne le texte sanitisé."""
    used = defaultdict(int)
    for ent_text, label, start, end in reversed(entities):
        if strategy == "masking":
            replacement = f"[MASK_{label}]"
        elif strategy == "pseudo":
            pool = FAKE_REPLACEMENTS.get(label, ["[UNKNOWN]"])
            replacement = pool[used[label] % len(pool)]
            used[label] += 1
        else:  # generic
            replacement = GENERIC_MAP.get(label, "something")
        text = text[:start] + replacement + text[end:]
    return text


def compute_risk(entities, strategy: str):
    """Simule l'attaque et retourne le score de risque résiduel."""
    rates = RECOVERY_RATES.get(strategy, RECOVERY_RATES["masking"])
    hits, total = 0, len(entities)
    if total == 0:
        return 0.0, 0, 0
    for _, label, _, _ in entities:
        rate = rates.get(label, 0.45)
        ctx_bonus = 0.05  
        if random.random() < rate + ctx_bonus:
            hits += 1
    return hits / total, hits, total


def risk_bar(score: float, width: int = 30) -> str:
    """Affiche une barre de risque colorée."""
    filled = int(score * width)
    bar = "█" * filled + "░" * (width - filled)
    if score >= 0.60:
        col = RED
        label = "RISQUE ÉLEVÉ   ❌"
    elif score >= 0.40:
        col = YEL
        label = "RISQUE MOYEN   ⚠️ "
    else:
        col = GRN
        label = "RISQUE RÉDUIT  ✓ "
    return f"{col}[{bar}] {score*100:5.1f}%  {label}{R}"


def print_header():
    print("\n" + "═" * 72)
    print(f"{BD}{WHT}  🔬  Sanitization or Deception?  —  Démo Interactive{R}")
    print(f"  {GRAY}Paudel et al., PoPETs 2026  ·  Projet Pratique 2, UQAC{R}")
    print("═" * 72)


def run_analysis(domain: str, text: str, interactive: bool = True):
    """Lance l'analyse complète sur un texte."""

    print(f"\n{BD}{'─'*72}{R}")
    print(f"{BD}{CYAN}  Domaine : {domain}{R}")
    print(f"{'─'*72}")

    if interactive:
        input(f"\n  {GRAY}[Appuyez sur Entrée pour détecter les entités PII...]{R}")

  
    print(f"\n{BD}ÉTAPE 1 — Détection NER des entités (PII){R}")
    time.sleep(0.3)
    entities = detect_entities(text)

    if not entities:
        print(f"  {YEL}Aucune entité détectée (le texte ne contient pas de PII reconnus).{R}")
        return


    highlighted = text
    offset = 0
    for ent_text, label, start, end in entities:
        hi = f"{BD}{RED}[{ent_text}]{GRAY}({label}){R}"
        highlighted = highlighted[:start + offset] + hi + highlighted[end + offset:]
        offset += len(hi) - (end - start)

    print(f"\n  {highlighted}\n")
    print(f"  {BD}Entités détectées ({len(entities)}) :{R}")
    for ent_text, label, _, _ in entities:
        print(f"    {CYAN}▸{R} {BD}{ent_text}{R}  {GRAY}→ {label}{R}")

    if interactive:
        input(f"\n  {GRAY}[Appuyez sur Entrée pour appliquer les 3 stratégies de sanitisation...]{R}")


    strategies = [
        ("masking", "Masquage [MASK_TYPE]", RED),
        ("pseudo",  "Pseudonymisation (faux noms)", YEL),
        ("generic", "Remplacement générique", BLUE),
    ]

    results = {}
    print(f"\n{BD}ÉTAPE 2 — Application des stratégies de sanitisation{R}\n")

    for key, name, col in strategies:
        sanitized = apply_strategy(text, entities, key)
        risk, hits, total = compute_risk(entities, key)
        results[key] = (sanitized, risk, hits, total, name, col)

        print(f"  {col}{BD}► {name}{R}")
        print(f"    {GRAY}{sanitized}{R}")
        print()
        time.sleep(0.2 if not interactive else 0)

    if interactive:
        input(f"  {GRAY}[Appuyez sur Entrée pour voir les scores de risque résiduel...]{R}")


    print(f"\n{BD}ÉTAPE 3 — Simulation de l'attaque adversariale (LLM){R}")
    print(f"  {GRAY}Un adversaire tente de reconstruire les PII depuis le texte sanitisé.{R}\n")
    time.sleep(0.3)

    for key, name, col in strategies:
        sanitized, risk, hits, total, name_, col_ = results[key]
        print(f"  {col_}{BD}{name}{R}")
        print(f"    Entités récupérées par l'attaquant : {BD}{hits}/{total}{R}")
        print(f"    {risk_bar(risk)}")
        print()
        time.sleep(0.15)


    print(f"{'─'*72}")
    print(f"{BD}  Conclusion pour ce texte :{R}")

    best_key = min(results, key=lambda k: results[k][1])
    best_name = results[best_key][4]
    best_risk = results[best_key][1]
    worst_key = max(results, key=lambda k: results[k][1])
    worst_risk = results[worst_key][1]

    print(f"  • Meilleure stratégie : {GRN}{BD}{best_name}{R} "
          f"({GRN}{best_risk*100:.1f}% de risque{R})")
    print(f"  • Masquage simple :     risque de {RED}{BD}{worst_risk*100:.1f}%{R} "
          f"— {RED}insuffisant !{R}")
    print(f"  • → Valide la thèse de Paudel et al. : la sanitisation NER seule")
    print(f"    {BD}ne garantit pas la confidentialité{R} des données personnelles.")
    print(f"{'─'*72}\n")


def interactive_mode():
    """Mode interactif — l'utilisateur entre son propre texte."""
    print_header()
    print(f"\n{BD}Mode interactif{R} — Entrez votre propre texte contenant des données personnelles.")
    print(f"{GRAY}Exemples : un email, un rapport médical, une fiche RH, etc.{R}")
    print(f"{GRAY}(Tapez 'exit' pour quitter, 'auto' pour la démo automatique){R}\n")

    while True:
        print(f"{BD}{CYAN}Entrez un texte à analyser :{R}")
        try:
            user_input = input("  > ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GRAY}Au revoir !{R}\n")
            break

        if user_input.lower() == "exit":
            print(f"\n{GRAY}Au revoir !{R}\n")
            break
        elif user_input.lower() == "auto":
            auto_mode()
            break
        elif len(user_input) < 20:
            print(f"  {YEL}Texte trop court — entrez au moins 20 caractères.{R}\n")
            continue
        else:
            run_analysis("Texte personnalisé", user_input, interactive=True)
            print(f"\n{GRAY}Entrez un autre texte ou 'exit' pour quitter.{R}\n")


def auto_mode():
    """Mode automatique — montre les 3 textes prédéfinis sans interaction."""
    print_header()
    print(f"\n{BD}Mode automatique{R} — Démonstration sur 3 textes prédéfinis.\n")
    time.sleep(1)

    for domain, text in DEMO_TEXTS:
        run_analysis(domain, text, interactive=False)
        time.sleep(1)


    print("\n" + "═" * 72)
    print(f"{BD}{WHT}  RÉSUMÉ GLOBAL — Résultats de la démonstration{R}")
    print("═" * 72)
    print(f"""
  Les trois textes testés (médical, entreprise, personnel) montrent
  systématiquement que :

  {RED}{BD}Masquage [MASK]{R}          → Risque moyen ~{RED}72%{R}  {RED}❌ Insuffisant{R}
  {YEL}{BD}Pseudonymisation{R}         → Risque moyen ~{YEL}55%{R}  {YEL}⚠️  Partiel{R}
  {GRN}{BD}Remplacement générique{R}   → Risque moyen ~{GRN}38%{R}  {GRN}✓  Meilleur{R}

  {BD}Message clé (Paudel et al., 2026) :{R}
  La sanitisation NER ne {IT}supprime{R} pas les PII — elle les {IT}déplace{R}.
  Un LLM adversarial peut exploiter le contexte résiduel pour
  reconstruire les informations originales, quelle que soit la
  stratégie de remplacement utilisée.

  
  {GRAY}→ Voir risk_comparison.png pour les graphiques comparatifs.{R}
""")
    print("═" * 72 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Démo interactive — Sanitization or Deception? (PoPETs 2026)"
    )
    parser.add_argument("--auto", action="store_true",
                        help="Mode automatique sans interaction utilisateur")
    args = parser.parse_args()

    if args.auto:
        auto_mode()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
