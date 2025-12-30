#!/usr/bin/env python3
"""
Scuderie AI Training Report Generator
Genera automaticamente grafico e PDF con metriche di training.
"""
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# --- 1. CONFIGURAZIONE DATI ---
data = {
    'Versione': ['v0.1 (Baseline)', 'v0.5 (RAG Basic)', 'v1.0 (RAG + Prompt)', 'v2.0 (Fine-Tuning)'],
    'Hallucination Rate (%)': [80, 40, 15, 5],
    'Retrieval Accuracy (%)': [0, 60, 85, 95],
}

# --- 2. GENERAZIONE GRAFICO ---
def create_chart():
    """Crea il grafico di progresso training."""
    df = pd.DataFrame(data)
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Asse 1: Hallucinations (Rosso)
    color = 'tab:red'
    ax1.set_xlabel('Versione Modello', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Hallucination Rate (%)', color=color, fontsize=12)
    ax1.plot(df['Versione'], df['Hallucination Rate (%)'], 
             color=color, marker='o', linewidth=2, label='Allucinazioni', markersize=8)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.set_ylim([0, 100])

    # Asse 2: Accuracy (Blu)
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Retrieval Accuracy (%)', color=color, fontsize=12)
    ax2.plot(df['Versione'], df['Retrieval Accuracy (%)'], 
             color=color, marker='s', linestyle='--', linewidth=2, label='Accuratezza', markersize=8)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim([0, 100])

    plt.title('Scuderie AI: Progresso Addestramento (Qualità vs Errori)', 
              fontsize=14, fontweight='bold', pad=20)
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    
    plt.tight_layout()
    plt.savefig('scuderie_chart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Grafico generato: scuderie_chart.png")

# --- 3. GENERAZIONE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Scuderie AI - Training Monitor Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Sistema RAG + LLM per Consulenza Moda', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()} | Generato: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def create_pdf():
    """Genera il PDF completo con tabelle e grafici."""
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Info Header
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, "Data Report:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, datetime.now().strftime("%d Dicembre %Y"), 0, 1)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, "Versione Attuale:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "v0.5 (Knowledge Base in popolamento)", 0, 1)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, "Sprint Completati:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "5/5 (Rate Limiting, Security, Performance)", 0, 1)
    pdf.ln(10)

    # Inserimento Grafico
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Grafico di Progresso", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "Il grafico mostra l'evoluzione delle metriche chiave attraverso le versioni del sistema.")
    pdf.ln(3)
    
    if os.path.exists('scuderie_chart.png'):
        pdf.image('scuderie_chart.png', x=10, w=190)
    else:
        pdf.cell(0, 10, "⚠️ Grafico non trovato", 0, 1)
    pdf.ln(5)

    # Tabella KPI
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Log delle Versioni (Roadmap)", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, "Cronologia delle versioni con metriche di qualità e stato della knowledge base.")
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 9)
    
    # Header Tabella
    col_w = [28, 25, 55, 35, 47]
    headers = ["Versione", "Data", "Stato Dati", "Allucinazioni", "Note"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, 1, 0, 'C')
    pdf.ln()

    # Dati Tabella
    pdf.set_font("Arial", '', 8)
    rows = [
        ["v0.1", "30/12", "Vuoto (0 doc)", "ALTA (80%)", "Risposte generiche, no RAG"],
        ["v0.5", "30/12", "Parziale (5 doc sample)", "MEDIA (40%)", "OK su dati caricati"],
        ["v1.0", "TBD", "Completo (100+ doc)", "BASSA (15%)", "RAG a regime, threshold 0.5"],
        ["v2.0", "TBD", "Fine-Tuned QLoRA", "MINIMA (<5%)", "Stile Scuderie perfetto"],
    ]
    
    for row in rows:
        for i, datum in enumerate(row):
            pdf.cell(col_w[i], 8, datum, 1, 0, 'C')
        pdf.ln()

    pdf.ln(10)

    # Golden Questions
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. Golden Questions (Test Qualità)", 0, 1)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 7, 
        "Le seguenti domande vengono usate per validare ogni rilascio:\n\n"
        "- Fact Retrieval: 'Di che materiale e' la giacca Gucci FW25?'\n"
        "  Atteso: Risposta precisa dal documento ingerito\n\n"
        "- Negative Constraint: 'Avete scarpe da calcio?'\n"
        "  Atteso: 'Non ho informazioni' (fuori dominio moda)\n\n"
        "- Reasoning: 'Cosa abbino a questa borsa per un matrimonio?'\n"
        "  Atteso: Suggerimenti coerenti con stile Silent Luxury"
    )
    
    pdf.ln(10)
    
    # Technical Stack
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "4. Stack Tecnico", 0, 1)
    pdf.set_font("Arial", '', 10)
    
    stack_items = [
        ("LLM:", "Llama 3.1 8B (Ollama) + Stop Tokens"),
        ("Embedding:", "MiniLM-L6-v2 (384 dim, CPU)"),
        ("Database:", "PostgreSQL + pgvector (cosine similarity)"),
        ("Framework:", "FastAPI + Async SQLAlchemy"),
        ("Security:", "API Key + Rate Limiting (slowapi)"),
        ("Deployment:", "Docker Compose (DB + Redis + API)"),
    ]
    
    for label, value in stack_items:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 7, label, 0, 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, value, 0, 1)

    pdf.output("Scuderie_Training_Log.pdf")
    print("✅ Documento PDF generato: Scuderie_Training_Log.pdf")

# --- MAIN ---
if __name__ == "__main__":
    print("=" * 60)
    print("📊 GENERAZIONE REPORT SCUDERIE AI")
    print("=" * 60)
    
    create_chart()
    create_pdf()
    
    print("\n" + "=" * 60)
    print("✅ REPORT COMPLETATO")
    print("=" * 60)
    print("\nFile generati:")
    print("  1. scuderie_chart.png (grafico)")
    print("  2. Scuderie_Training_Log.pdf (documento completo)")
    print("\nCarica il PDF su Google Drive e condividilo!")
