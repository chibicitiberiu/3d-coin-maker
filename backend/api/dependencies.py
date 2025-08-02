"""
FastAPI Dependency Injection

Provides dependency injection for FastAPI routes using the new
service container system.
"""

from fastapi import Depends, HTTPException, Request

from core.interfaces.task_queue import TaskQueue
from core.service_container import ServiceContainer
from core.services.coin_generation_service import CoinGenerationService


def get_services(request: Request) -> ServiceContainer:
    """Get the service container from the FastAPI app state."""
    if not hasattr(request.app.state, 'services'):
        raise HTTPException(
            status_code=500,
            detail="Services not available - application not properly initialized"
        )
    return request.app.state.services


# Create dependency singletons at module level
_services_dep = Depends(get_services)

def get_coin_service(services: ServiceContainer = _services_dep) -> CoinGenerationService:
    """Get the coin generation service instance."""
    return services.get_coin_service()


def get_task_queue(services: ServiceContainer = _services_dep) -> TaskQueue:
    """Get the task queue instance."""
    return services.get_task_queue()


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
# Note: These should be used in function parameters like: coin_service: CoinGenerationService = CoinServiceDep
CoinServiceDep = Depends(get_coin_service)
TaskQueueDep = Depends(get_task_queue)
ClientIPDep = Depends(get_client_ip)
ServicesDep = Depends(get_services)
