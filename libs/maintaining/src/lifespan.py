"""Maintaining Lib — Orchestration Layer

Orchestrates arbitraging lib for data synchronization
"""

from injector import Injector, Module, provider, singleton

from libs.arbitraging.src.ports.sync_catalog_port import SyncCatalogPort
from libs.arbitraging.src.ports.sync_reference_data_port import SyncReferenceDataPort
from libs.arbitraging.src.lifespan import configure as configure_arbitraging
from libs.maintaining.src.application.commands.sync_data_command import SyncDataCommand
from libs.maintaining.src.ports.sync_data_port import SyncDataPort


class MaintainingModule(Module):
    """Maintaining DI Configuration"""

    @singleton
    @provider
    def provide_sync_data(
        self,
        sync_catalog: SyncCatalogPort,
        sync_reference: SyncReferenceDataPort,
    ) -> SyncDataPort:
        return SyncDataCommand(
            sync_catalog=sync_catalog,
            sync_reference=sync_reference,
        )


_injector: Injector | None = None


def startup() -> Injector:
    """Start DI container"""
    global _injector
    _injector = Injector(
        [
            configure_arbitraging,
            MaintainingModule(),
        ]
    )
    return _injector


def shutdown() -> None:
    """Shutdown and release resources"""
    global _injector
    _injector = None


def get_injector() -> Injector:
    """Get DI container, auto-start if not initialized"""
    global _injector
    if _injector is None:
        startup()
    return _injector
