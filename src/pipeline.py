"""CLI runner for benchmarking 2D spatial document parsing & checksum accuracy."""

import argparse
import time
from src.generator import generate_synthetic_spec_document
from src.parser import EngineeringDocumentParser


def run_benchmark(n_documents: int = 50):
    print("=" * 68)
    print("MULTIMODAL DOCUMENT INTELLIGENCE: SPATIAL LAYOUT & CHECKSUM BENCHMARK")
    print("=" * 68)

    parser = EngineeringDocumentParser()
    total_truth_items = 0
    total_parsed_items = 0
    correctly_extracted_items = 0
    checksums_passed = 0
    po_matched = 0

    t0 = time.time()
    for seed in range(n_documents):
        tokens, truth = generate_synthetic_spec_document(seed=seed + 100)
        res = parser.parse_document(tokens)

        # Check PO number
        if res.po_number == truth["po_number"]:
            po_matched += 1

        # Check mathematical checksum
        if res.checksum_passed:
            checksums_passed += 1

        truth_parts = {item["part_number"]: item for item in truth["items"]}
        total_truth_items += len(truth["items"])
        total_parsed_items += len(res.line_items)

        for p_item in res.line_items:
            if p_item.part_number in truth_parts:
                t_item = truth_parts[p_item.part_number]
                if p_item.qty == t_item["qty"] and abs(p_item.unit_price - t_item["unit_price"]) < 0.05:
                    correctly_extracted_items += 1

    elapsed = time.time() - t0
    precision = (correctly_extracted_items / max(total_parsed_items, 1)) * 100.0
    recall = (correctly_extracted_items / max(total_truth_items, 1)) * 100.0
    f1 = (2 * precision * recall) / max(precision + recall, 1e-6)
    checksum_rate = (checksums_passed / n_documents) * 100.0
    po_acc = (po_matched / n_documents) * 100.0
    latency_ms = (elapsed / n_documents) * 1000.0

    print(f"\nEvaluated {n_documents} complex engineering procurement documents:")
    print(f"  Item Precision               : {precision:5.1f}%")
    print(f"  Item Recall                  : {recall:5.1f}%")
    print(f"  Item Extraction F1-Score     : {f1:5.1f}%")
    print(f"  PO Number Accuracy           : {po_acc:5.1f}%")
    print(f"  Arithmetic Checksum Pass Rate: {checksum_rate:5.1f}%")
    print(f"  Average Processing Latency   : {latency_ms:5.2f} ms / document")
    print("\n[SUCCESS] Document intelligence benchmark completed successfully.")


if __name__ == "__main__":
    cli_parser = argparse.ArgumentParser(description="Document Intelligence Benchmark")
    cli_parser.add_argument("--docs", type=int, default=50, help="Number of documents")
    args = cli_parser.parse_args()
    run_benchmark(n_documents=args.docs)
