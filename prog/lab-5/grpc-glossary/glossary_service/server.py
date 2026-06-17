"""gRPC-сервер GlossaryService: пять операций CRUD над глоссарием."""
import os
import sys
from concurrent import futures

import grpc

# Делаем сгенерированные модули из gen/ импортируемыми.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gen"))

import glossary_pb2  # noqa: E402
import glossary_pb2_grpc  # noqa: E402

from glossary_service import db  # noqa: E402


def _to_proto(row) -> glossary_pb2.Term:
    return glossary_pb2.Term(
        id=row.id, term=row.term, definition=row.definition, category=row.category or ""
    )


class GlossaryServicer(glossary_pb2_grpc.GlossaryServiceServicer):
    def ListTerms(self, request, context):
        session = db.SessionLocal()
        try:
            rows = session.query(db.Term).order_by(db.Term.term).all()
            return glossary_pb2.TermList(terms=[_to_proto(r) for r in rows])
        finally:
            session.close()

    def GetTerm(self, request, context):
        session = db.SessionLocal()
        try:
            row = db.find(session, request.term)
            if row is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Термин '{request.term}' не найден")
            return _to_proto(row)
        finally:
            session.close()

    def AddTerm(self, request, context):
        if not request.term.strip() or not request.definition.strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "term и definition обязательны")
        session = db.SessionLocal()
        try:
            if db.find(session, request.term) is not None:
                context.abort(
                    grpc.StatusCode.ALREADY_EXISTS,
                    f"Термин '{request.term}' уже существует",
                )
            row = db.Term(
                term=request.term.strip(),
                definition=request.definition.strip(),
                category=request.category.strip() or None,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return _to_proto(row)
        finally:
            session.close()

    def UpdateTerm(self, request, context):
        if not request.definition.strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "definition обязателен")
        session = db.SessionLocal()
        try:
            row = db.find(session, request.term)
            if row is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Термин '{request.term}' не найден")
            row.definition = request.definition.strip()
            row.category = request.category.strip() or None
            session.commit()
            session.refresh(row)
            return _to_proto(row)
        finally:
            session.close()

    def DeleteTerm(self, request, context):
        session = db.SessionLocal()
        try:
            row = db.find(session, request.term)
            if row is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Термин '{request.term}' не найден")
            session.delete(row)
            session.commit()
            return glossary_pb2.DeleteReply(message=f"Термин '{request.term}' удалён")
        finally:
            session.close()


def serve():
    db.init_db()  # авто-миграция и наполнение при старте
    port = os.getenv("PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    glossary_pb2_grpc.add_GlossaryServiceServicer_to_server(GlossaryServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"GlossaryService слушает на порту {port}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
