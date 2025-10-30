#!/bin/bash
# Safe quarantine script - moves files to __quarantine__/20251030/

QUAR_BASE="__quarantine__/20251030"

# Ingestion scripts
for f in ingest_b1_amendment13.py ingest_building_code.py ingest_full_building_code.py \
         ingest_full_metal_roofing.py ingest_metal_roofing.py ingest_metal_roofing_quick.py \
         ingest_nzs4229.py monitor_ingestion.py tier1_pdf_ingestion.py tier1_production_ingestion.py; do
  [ -f "$f" ] && git mv "$f" "../${QUAR_BASE}/ingestion/"
done

# Enrichment scripts
for f in auto_loop_enrichment.py batch_enrichment.py complete_metadata_enrichment.py \
         complete_metadata_extraction.py extract_metadata.py interactive_enrichment.py \
         phase2_coverage_extension.py phase3_final_uplift.py safe_metadata_uplift.py \
         self_monitoring_enrichment.py simple_monitoring_enrichment.py snippet_priority_enrichment.py; do
  [ -f "$f" ] && git mv "$f" "../${QUAR_BASE}/enrichment/"
done

# QA/Testing scripts
for f in chat_production_validation.py focused_production_qa.py production_qa.py \
         seed_test_docs.py seed_test_docs_mock.py stryda_production_soak.py; do
  [ -f "$f" ] && git mv "$f" "../${QUAR_BASE}/qa_testing/"
done

# Utilities
for f in enhanced_retriever.py hybrid_retrieval.py multi_turn_chat.py \
         safe_corpus_expansion.py snippet_focus.py type_safety.py update_embeddings.py; do
  [ -f "$f" ] && git mv "$f" "../${QUAR_BASE}/utilities/"
done

# Logs and temp
[ -f "../simple_backend.log" ] && git mv "../simple_backend.log" "../${QUAR_BASE}/utilities/"
[ -d "tmp" ] && git mv "tmp" "../${QUAR_BASE}/utilities/"

echo "✅ Quarantine complete"
