from typing import Annotated

from fastapi import Depends, Request

from app.collector import Collector


def get_collector(request: Request) -> Collector:
    """Background price collector created in lifespan."""
    return request.app.state.collector


CollectorDep = Annotated[Collector, Depends(get_collector)]
