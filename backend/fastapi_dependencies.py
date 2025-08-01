"""
FastAPI Dependency Injection

Provides dependency injection for FastAPI routes using the existing
application container and services.
"""

from fastapi import Depends, Request

from core.containers.application import container
from core.interfaces.task_queue import TaskQueue
from core.services.coin_generation_service import CoinGenerationService


def get_coin_service() -> CoinGenerationService:
    """Get the coin generation service instance."""
    return container.coin_generation_service()


def get_task_queue() -> TaskQueue:
    """Get the task queue instance."""
    return container.task_queue()


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded headers first
    x_forwarded_for = request.headers.get('x-forwarded-for')
    if x_forwarded_for:
        # Take the first IP in the chain
        ip = x_forwarded_for.split(',')[0].strip()
        return ip

    # Check other common forwarding headers
    x_real_ip = request.headers.get('x-real-ip')
    if x_real_ip:
        return x_real_ip.strip()

    # Fall back to client IP
    if hasattr(request, 'client') and request.client:
        return request.client.host

    # Final fallback
    return '127.0.0.1'


# Dependency aliases for cleaner route signatures
CoinServiceDep = Depends(get_coin_service)
TaskQueueDep = Depends(get_task_queue)
ClientIPDep = Depends(get_client_ip)
