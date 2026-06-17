"""Демонстрационный gRPC-клиент: обращается к обоим сервисам."""
import os
import sys

import grpc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gen"))

import glossary_pb2  # noqa: E402
import glossary_pb2_grpc  # noqa: E402
import recommendation_pb2  # noqa: E402
import recommendation_pb2_grpc  # noqa: E402

GLOSSARY_ADDR = os.getenv("GLOSSARY_ADDR", "localhost:50051")
RECO_ADDR = os.getenv("RECO_ADDR", "localhost:50052")


def main():
    gl = glossary_pb2_grpc.GlossaryServiceStub(grpc.insecure_channel(GLOSSARY_ADDR))
    rc = recommendation_pb2_grpc.RecommendationServiceStub(grpc.insecure_channel(RECO_ADDR))

    print("== GlossaryService ==")
    all_terms = gl.ListTerms(glossary_pb2.Empty()).terms
    print(f"Всего терминов: {len(all_terms)}")

    print("\nGetTerm('decorator'):")
    t = gl.GetTerm(glossary_pb2.TermKey(term="decorator"))
    print(f"  {t.term} [{t.category}] — {t.definition}")

    print("\nAddTerm('Slicing'):")
    t = gl.AddTerm(glossary_pb2.NewTerm(
        term="Slicing", definition="Срез последовательности.", category="Синтаксис"))
    print(f"  создан id={t.id}: {t.term}")

    print("\nUpdateTerm('Slicing'):")
    t = gl.UpdateTerm(glossary_pb2.UpdateTermRequest(
        term="Slicing", definition="Получение подпоследовательности [start:stop:step].",
        category="Основы"))
    print(f"  обновлён: {t.definition} [{t.category}]")

    print("\nDeleteTerm('Slicing'):")
    print(f"  {gl.DeleteTerm(glossary_pb2.TermKey(term='Slicing')).message}")

    print("\n== RecommendationService (клиент GlossaryService) ==")
    cats = rc.ListCategories(glossary_pb2.Empty()).categories
    print(f"Категории: {', '.join(cats)}")

    print("\nRecommendByCategory('ООП'):")
    for t in rc.RecommendByCategory(recommendation_pb2.CategoryRequest(category="ООП")).terms:
        print(f"  - {t.term}: {t.definition}")

    print("\nRandomTerms(3):")
    for t in rc.RandomTerms(recommendation_pb2.RandomRequest(count=3)).terms:
        print(f"  - {t.term} [{t.category}]")

    print("\n== Обработка ошибок ==")
    try:
        gl.GetTerm(glossary_pb2.TermKey(term="nope"))
    except grpc.RpcError as e:
        print(f"  GetTerm('nope') -> {e.code().name}: {e.details()}")


if __name__ == "__main__":
    main()
