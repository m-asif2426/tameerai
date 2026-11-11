"""
TameerAI - Construction Material Rate Source Adapters Package (Stage 2B)

Exposes concrete, production-grade source adapters and connectors across
Pakistani national, provincial, marketplace, and direct dealer data providers.
"""

from app.services.material_rates.adapters.pbs_adapter import PbsStatisticalSourceAdapter
from app.services.material_rates.adapters.nha_schedule_adapter import NhaScheduleSourceAdapter
from app.services.material_rates.adapters.zarea_adapter import ZareaMarketplaceSourceAdapter
from app.services.material_rates.adapters.materialrate_adapter import MaterialRatePublisherSourceAdapter
from app.services.material_rates.adapters.steelratetoday_adapter import SteelRateTodaySourceAdapter
from app.services.material_rates.adapters.gharhub_adapter import GharHubPublisherSourceAdapter
from app.services.material_rates.adapters.dealer_connector import DirectDealerConnector

__all__ = [
    "PbsStatisticalSourceAdapter",
    "NhaScheduleSourceAdapter",
    "ZareaMarketplaceSourceAdapter",
    "MaterialRatePublisherSourceAdapter",
    "SteelRateTodaySourceAdapter",
    "GharHubPublisherSourceAdapter",
    "DirectDealerConnector",
]

