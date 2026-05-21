from sqlalchemy.orm import Query, Session


def tenant_scoped_query(db_session: Session, model_class, tenant_id: str) -> Query:
    return db_session.query(model_class).filter(model_class.tenant_id == tenant_id)  # type: ignore[no-any-return]
