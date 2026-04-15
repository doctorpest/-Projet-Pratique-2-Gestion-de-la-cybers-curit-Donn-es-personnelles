# Projet Pratique 2 : Gestion de la cybersécurité / Données personnelles
## UQAC — Avril 2026

---

## 📄 L'article analysé

**"Sanitization or Deception? Rethinking Privacy Protection in Large Language Models"**  
Bipin Paudel, Bishwas Mandal, George T. Amariucai (Kansas State University)  
Shuangqing Wei (Louisiana State University)  
*Proceedings on Privacy Enhancing Technologies (PoPETs) 2026, Article #0009, pp. 154–174*

---

## 🧠 Compréhension de l'article

### Le problème de départ

Quand une organisation utilise un LLM externe (ChatGPT, Gemini, Copilot…), elle doit
souvent lui envoyer des textes contenant des données personnelles : noms de patients,
numéros de dossiers, salaires, adresses. La réglementation (GDPR, HIPAA, PIPEDA) interdit
de transmettre ces données à des tiers sans protection.

La solution standard dans l'industrie est la **sanitisation par NER** :
1. Un outil de reconnaissance d'entités nommées (Named Entity Recognition) détecte les PII
2. Il les remplace avant d'envoyer le texte au LLM

```
AVANT : "Patient Marie Dupont, née 14 mars 1985, dossier #MCH-2024-00442"
APRÈS : "Patient [MASK], née [MASK], dossier [MASK]"
```

### La thèse centrale

Paudel et al. démontrent que **cette pratique donne une fausse impression de sécurité**.

La sanitisation NER ne *supprime* pas les PII elle les *déplace*. Le contexte résiduel
(structure grammaticale, verbes, déterminants, cohérence sémantique) permet à un LLM
adversarial de "remplir les blancs" avec une précision bien supérieure au hasard.

Exemple : le texte sanitisé `"[MASK] at [MASK] has scheduled a follow-up for patient
[MASK] regarding his hypertension treatment"` révèle encore :
- Premier MASK = probablement un médecin
- Deuxième MASK = probablement un hôpital
- "his" = patient masculin
- "hypertension" = domaine cardiovasculaire

Un adversaire avec des données auxiliaires peut ré-identifier la personne.

### Contributions du papier

**1. Taxonomy des attaques sur texte sanitisé**
Les auteurs classifient les attaques en trois niveaux :
- Reconstruction directe (deviner l'entité exacte)
- Inférence contextuelle (déduire la catégorie sans valeur exacte)
- Ré-identification combinatoire (croiser avec des données externes)

**2. L'attaque NER-fool**
Démonstration empirique qu'un LLM peut reconstruire les entités masquées en exploitant
le contexte résiduel, avec une précision significativement supérieure au hasard sur tous
les types de substitution testés.

**3. Score de risque résiduel**
Une métrique quantitative continue (0 = sûr, 1 = compromis) qui mesure la quantité
d'information identifiable restant après sanitisation — au-delà de la simple
présence/absence de tokens PII.

**4. Recommandations pratiques**
Guidelines pour les développeurs : quels types de PII sont les plus vulnérables, dans
quelles conditions la sanitisation est insuffisante, quelles mesures complémentaires
sont nécessaires.

### Limitations explicites (dites par les auteurs)

| Limitation | Détail |
|---|---|
| Langue | Expériences en anglais uniquement. Langues morphologiquement riches (français, arabe) non testées |
| Corpus | Ensemble de datasets limité domaines médical, juridique, financier ont des PII structurellement différents |
| Modèles LLM | Testés avec des modèles actuels. Modèles futurs plus puissants aggraveront le risque |
| Déploiement | Le score de risque résiduel n'est pas encore intégré dans des outils industriels |

### Limitations implicites (identifiées à l'analyse critique)

| Limitation | Pourquoi c'est important |
|---|---|
| Adversaire passif uniquement | Un adversaire actif (prompt injection) est plus dangereux et non adressé |
| PII formels seulement | Les PII implicites (descriptions comportementales, contexte temporel) échappent aux NER |
| Métrique non granulaire | Remplacer un prénom est traité comme remplacer un numéro de sécurité sociale |
| Aucune évaluation humaine | Un vrai test avec des humains pourrait invalider certaines conclusions |

---

## 🎯 Perspective choisie

**Évaluation automatisée de la robustesse post-sanitisation**

Le papier propose théoriquement un score de risque résiduel mais ne fournit pas d'outil
pour le calculer sur n'importe quelle combinaison texte + stratégie. Notre démo comble
ce vide en construisant un benchmark qui compare les trois stratégies de sanitisation
les plus courantes face à une attaque adversariale simulée.

**Pourquoi cette perspective :**
1. Directement issue des limitations du papier (les auteurs l'appellent explicitement)
2. Elle rend le résultat théorique concret et exécutable
3. Elle couvre une limitation implicite : le papier ne compare pas les stratégies entre elles
4. Implémentable sans infrastructure lourde (Python + spaCy)

---

## 📁 Fichiers du projet

| Fichier | Description |
|---|---|
| `demo_live.py` | Démo interactive pour la présentation orale en classe |
| `sanitization_deception_slides.pptx` | Présentation PowerPoint |
| `generate_graph.py`  | Génère le graphique comparatif |
| `risk_comparison.png` | Graphique des résultats |
| `install.sh` | Script d'installation automatique |
| `README.md` | Ce fichier |

---

## 🚀 Installation et exécution

### Installation

```bash
# Installation automatique
bash install.sh

# Ou manuellement :
pip install spacy matplotlib tabulate
python -m spacy download en_core_web_sm
```

> **Sans spaCy :** le script bascule automatiquement sur un détecteur regex fonctionnel,
> moins précis. Aucune erreur ne sera levée.

### Exécution

```bash

# Démo automatique
python demo_live.py --auto

```

---

## 📊 Résultats et interprétation

| Stratégie | Risque moyen | Verdict |
|---|---|---|
| Masquage `[MASK]` | ~73% | Insuffisant — le contexte syntaxique suffit à l'attaquant |
| Pseudonymisation | ~58% | Partiel — réduit le risque mais reste vulnérable |
| Remplacement générique | ~44% | Meilleur — mais détruit partiellement l'utilité du texte |

**Conclusion :** Aucune stratégie NER seule ne ramène le risque sous 30%. Cela confirme
la thèse du papier : la sanitisation NER est nécessaire mais pas suffisante. Des mesures
complémentaires (differential privacy textuelle, vérification du risque résiduel) sont
indispensables pour une vraie protection.

---

## 📚 Références

- Paudel et al. (2026). *Sanitization or Deception? Rethinking Privacy Protection in
  Large Language Models*. PoPETs 2026(1), pp. 154–174.
- Staab et al. (2024). *Beyond Memorization: Violating Privacy via Inference with Large
  Language Models*. ICLR 2024.
- Honnibal et al. (2020). *spaCy: Industrial-strength Natural Language Processing*.
- Dwork & Roth (2014). *The Algorithmic Foundations of Differential Privacy*.

---

## 👥 Équipe

- Ayat Allah EL Anouar
- Elmamoune Mikou

**Contact enseignant :** Samuel Desbiens — s6desbie@uqac.ca — Bureau P4-6465
**Date de remise :** Mercredi 15 avril 2026, 19h00
