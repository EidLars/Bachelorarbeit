# Greenwashing Detection Pipeline

Dieser neue Ansatz setzt komplett auf offene Modelle: ClimateBERT für die Claim-Erkennung und DeepSeek R1 Zero über OpenRouter für die Konsistenzbewertung. Die Pipeline verarbeitet Nachhaltigkeits- oder Geschäftsberichte (PDF), extrahiert mögliche Green Claims, sammelt dazugehörige Finanz- und Emissionskennzahlen und bewertet anschließend, ob Widersprüche bzw. Greenwashing-Indikationen vorliegen.

## Architekturüberblick

1. **Dokumenten-Layer** (`PDFDocumentLoader`)
   - Liest PDF-Berichte und erzeugt pro Seite normalisierte Textabschnitte.
2. **Claim-Erkennung** (`ClaimExtractor`)
   - Nutzt `climatebert/distilroberta-base-climate-fever` via `transformers`.
   - Klassifiziert einzelne Sätze und markiert relevante Climate-Claims.
3. **KPI-Extraktion** (`KPIExtractor`)
   - Regex-basierte Heuristiken für Scope 1/2/3, Gesamtemissionen, Reduktionsraten und erneuerbare Energien.
   - Liefert strukturierte Datensätze inkl. Seitenreferenz.
4. **LLM-Evaluation** (`ConsistencyEvaluator`)
   - Ruft DeepSeek R1 Zero über die OpenRouter API auf.
   - Bewertet Konsistenz, Greenwashing-Risiko, Confidence und referenziert verwendete KPIs.
5. **Pipeline-Orchestrierung** (`GreenwashingPipeline`)
   - Verknüpft alle Bausteine und stellt JSON-Ausgaben für Reports bereit.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Benötigte Abhängigkeiten
- `transformers`
- `torch` (für das ClimateBERT-Modell)
- `pdfplumber`
- `requests`

Alle Pakete sind in `requirements.txt` hinterlegt.

## Konfiguration

1. **OpenRouter API Key**
   - Erstelle eine Umgebungsvariable `OPENROUTER_API_KEY` mit deinem persönlichen Schlüssel.
   - Beispiel (macOS/Linux):
     ```bash
     export OPENROUTER_API_KEY="sk-..."
     ```
2. **Modelle**
   - Standardmäßig nutzt die Pipeline `climatebert/distilroberta-base-climate-fever` und `deepseek/deepseek-r1-zero`.
   - Anpassungen können in `src/greenwashing_pipeline/config.py` vorgenommen werden.

## Ausführung

Die Pipeline lässt sich über das Skript `scripts/run_pipeline.py` starten.

```bash
python scripts/run_pipeline.py "ESG Reports" --output results.json --max-pages 5
```

Optionen:
- `--skip-evaluation`: Nur Claims und KPIs extrahieren (kein DeepSeek-Aufruf).
- `--max-pages`: Beschränkt die Seitenzahl pro Dokument für schnellere Tests.

Das Skript erstellt eine JSON-Datei mit allen gefundenen Claims, KPIs und – sofern aktiviert – Konsistenzbewertungen.

## Modulare Nutzung in Notebooks

```python
from greenwashing_pipeline.pipeline import GreenwashingPipeline
from greenwashing_pipeline.llm_evaluator import ConsistencyEvaluator

pipeline = GreenwashingPipeline(evaluator=ConsistencyEvaluator(), max_pages=3)
result = pipeline.process("ESG Reports/sample.pdf")
print(result.to_dict())
```

## Weiterentwicklung

- Ausbau der KPI-Erkennung (z. B. CAPEX/OPEX, Lieferkettenkennzahlen).
- Ergänzung weiterer ClimateBERT-Modelle oder Fine-Tuning.
- Qualitätsmetriken und Benchmark-Datensätze integrieren.
- Optionaler RAG-Schritt, um zusätzliche Kontextpassagen für das LLM bereitzustellen.

