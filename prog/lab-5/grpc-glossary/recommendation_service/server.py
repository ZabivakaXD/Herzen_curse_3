"""gRPC-сервер RecommendationService.

Сам выступает gRPC-клиентом GlossaryService: получает термины и формирует
рекомендации (по категории, случайные, список категорий).
"""
import os
import random
import sys
from concurrent import futures

import grpc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gen"))

import glossary_pb2  # noqa: E402
import glossary_pb2_grpc  # noqa: E402
import recommendation_pb2  # noqa: E402
import recommendation_pb2_grpc  # noqa: E402

# Адрес сервиса глоссария (в docker compose — имя сервиса glossary).
GLOSSARY_ADDR = os.getenv("GLOSSARY_ADDR", "localhost:50051")


def _fetch_all_terms():
    """Запрашивает все термины у GlossaryService по gRPC."""
    with grpc.insecure_channel(GLOSSARY_ADDR) as channel:
        stub = glossary_pb2_grpc.GlossaryServiceStub(channel)
        return list(stub.ListTerms(glossary_pb2.Empty()).terms)


class RecommendationServicer(recommendation_pb2_grpc.RecommendationServiceServicer):
    def RecommendByCategory(self, request, context):
        wanted = request.category.strip().lower()
        terms = [t for t in _fetch_all_terms() if t.category.lower() == wanted]
        if not terms:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Нет терминов в категории '{request.category}'",
            )
        return recommendation_pb2.RecommendReply(terms=terms)

    def RandomTerms(self, request, context):
        count = request.count if request.count > 0 else 3
        terms = _fetch_all_terms()
        random.shuffle(terms)
        return recommendation_pb2.RecommendReply(terms=terms[:count])

    def ListCategories(self, request, context):
        cats = sorted({t.category for t in _fetch_all_terms() if t.category})
        return recommendation_pb2.CategoryList(categories=cats)


def serve():
    port = os.getenv("PORT", "50052")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    recommendation_pb2_grpc.add_RecommendationServiceServicer_to_server(
        RecommendationServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(
        f"RecommendationService слушает на порту {port} "
        f"(глоссарий: {GLOSSARY_ADDR})",
        flush=True,
    )
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
