#!/usr/bin/env python3
"""
JSON Knowledge Base Import Script
Carica documenti da file JSON/JSONL nel database Scuderie AI.
"""
import json
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict
import sys


class JSONImporter:
    """Importa documenti JSON nel database via API."""
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = "scuderie-dev-key-2024"):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        self.stats = {"success": 0, "failed": 0, "total": 0}
    
    async def load_json_file(self, file_path: Path) -> List[Dict]:
        """Carica documenti da file JSON o JSONL."""
        documents = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Verifica se è JSONL (una riga = un JSON)
            first_line = f.readline()
            f.seek(0)
            
            if first_line.strip().startswith('{'):
                # JSONL format
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            doc = json.loads(line)
                            documents.append(doc)
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Errore riga {line_num}: {e}")
            else:
                # Standard JSON array
                try:
                    data = json.load(f)
                    documents = data if isinstance(data, list) else [data]
                except json.JSONDecodeError as e:
                    print(f"❌ Errore parsing JSON: {e}")
                    return []
        
        return documents
    
    async def ingest_document(self, doc: Dict, client: httpx.AsyncClient) -> bool:
        """Invia un documento all'API di ingest."""
        # Valida campi richiesti
        if not all(k in doc for k in ["source_id", "source_type", "content"]):
            print(f"⚠️  Documento senza campi richiesti: {doc.get('source_id', 'unknown')}")
            return False
        
        try:
            response = await client.post(
                f"{self.api_url}/api/v1/ingest",
                json=doc,
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                chunks = result.get("chunks", 1)
                print(f"✅ {doc['source_id']}: {chunks} chunk(s)")
                return True
            else:
                print(f"❌ {doc['source_id']}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ {doc['source_id']}: {e}")
            return False
    
    async def import_batch(self, documents: List[Dict], batch_size: int = 10):
        """Importa documenti in batch."""
        async with httpx.AsyncClient() as client:
            # Verifica connessione API
            try:
                health = await client.get(f"{self.api_url}/api/v1/health")
                if health.status_code != 200:
                    print("❌ Backend non raggiungibile!")
                    return
            except Exception as e:
                print(f"❌ Errore connessione: {e}")
                return
            
            print(f"\n📤 Importazione {len(documents)} documenti...")
            
            self.stats["total"] = len(documents)
            
            # Processa in batch
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                tasks = [self.ingest_document(doc, client) for doc in batch]
                results = await asyncio.gather(*tasks)
                
                self.stats["success"] += sum(results)
                self.stats["failed"] += len(results) - sum(results)
                
                print(f"Progress: {i + len(batch)}/{len(documents)}")
    
    def print_summary(self):
        """Stampa riepilogo importazione."""
        print("\n" + "="*50)
        print("📊 RIEPILOGO IMPORTAZIONE")
        print("="*50)
        print(f"Totale:    {self.stats['total']}")
        print(f"✅ Success: {self.stats['success']}")
        print(f"❌ Failed:  {self.stats['failed']}")
        print(f"Success rate: {self.stats['success']/max(self.stats['total'], 1)*100:.1f}%")
        print("="*50)


async def main():
    """Entry point."""
    if len(sys.argv) < 2:
        print("Usage: python import_json.py <file.json>")
        print("\nFormato JSON richiesto:")
        print('[{"source_id": "doc1", "source_type": "catalogo", "content": "..."}]')
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ File non trovato: {file_path}")
        sys.exit(1)
    
    importer = JSONImporter()
    documents = await importer.load_json_file(file_path)
    
    if not documents:
        print("❌ Nessun documento da importare")
        sys.exit(1)
    
    print(f"📁 Caricati {len(documents)} documenti da {file_path.name}")
    
    await importer.import_batch(documents, batch_size=5)
    importer.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
