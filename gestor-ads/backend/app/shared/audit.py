from __future__ import annotations

import functools
import logging
from typing import Any

logger = logging.getLogger(__name__)


def audit_write(action: str, entity: str):
    """Decorator for MetaAdsClient write methods.

    Expects the instance (self) to have:
      - _audit_fn: async callable or None
      - _user_id: str

    Calls _audit_fn with action, entity, request, response, error after the method.
    """

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            request_data: Any = None
            if args:
                request_data = args[0]
                if hasattr(request_data, "model_dump"):
                    request_data = request_data.model_dump()
                elif hasattr(request_data, "to_dict"):
                    request_data = request_data.to_dict()
            elif kwargs:
                request_data = dict(kwargs)

            response_data: Any = None
            error_msg: str | None = None

            try:
                response_data = await fn(self, *args, **kwargs)
                return response_data
            except Exception as exc:
                error_msg = str(exc)
                raise
            finally:
                if getattr(self, "_audit_fn", None) is not None:
                    try:
                        await self._audit_fn(
                            user_id=getattr(self, "_user_id", "unknown"),
                            action=action,
                            entity=entity,
                            request=request_data,
                            response=response_data,
                            error=error_msg,
                        )
                    except Exception:
                        logger.exception("Failed to write audit log for %s/%s", action, entity)

        return wrapper

    return decorator
