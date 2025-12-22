import torch
import sqlalchemy
from sqlalchemy import text

def run_check():
    print("\n--- 🚀 CHECK SISTEMA SCUDERIE ---")
    
    # 1. CHECK GPU (Apple Silicon)
    print(f"1. PyTorch Version: {torch.__version__}")
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        x = torch.ones(1, device=device)
        print("   ✅ ACCELERAZIONE GPU (MPS): ATTIVA")
    else:
        print("   ❌ ACCELERAZIONE GPU: NON RILEVATA")

    # 2. CHECK DATABASE
    db_url = "postgresql://scuderie_user:scuderie_password@localhost:5432/scuderie_db"
    try:
        engine = sqlalchemy.create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("   ✅ DATABASE: CONNESSO")
            
            # Attiviamo l'estensione vettoriale se non c'è
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("   ✅ ESTENSIONE PGVECTOR: ATTIVA")
                    
    except Exception as e:
        print(f"   ❌ ERRORE DATABASE: {e}")
        print("      (Controlla che Docker Desktop sia aperto e il container verde)")

    print("--- FINE CHECK ---\n")

if __name__ == "__main__":
    run_check()