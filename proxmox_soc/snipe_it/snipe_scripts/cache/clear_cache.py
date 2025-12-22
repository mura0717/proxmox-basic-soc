""" Clear Snipe-IT API Service Caches Script """

from proxmox_soc.asset_engine.asset_finder import AssetFinder
from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.snipe_it.snipe_api.services.status_labels import StatusLabelService
from proxmox_soc.snipe_it.snipe_api.services.categories import CategoryService
from proxmox_soc.snipe_it.snipe_api.services.manufacturers import ManufacturerService
from proxmox_soc.snipe_it.snipe_api.services.models import ModelService
from proxmox_soc.snipe_it.snipe_api.services.locations import LocationService
from proxmox_soc.snipe_it.snipe_api.services.fields import FieldService
from proxmox_soc.snipe_it.snipe_api.services.fieldsets import FieldsetService

class SnipeCacheClearer:
    
    def __init__(self):
        self.asset_service = AssetService()
        self.status_service = StatusLabelService()
        self.category_service = CategoryService()
        self.manufacturer_service = ManufacturerService()
        self.model_service = ModelService()
        self.location_service = LocationService()
        self.finder = AssetFinder(self.asset_service)
        self.field_service = FieldService()
        self.fieldset_service = FieldsetService()        
        
    def clear_all_caches(self):
        """Clears the internal caches of all services to ensure fresh data."""
        print("Clearing all local service caches...")
        self.asset_service._cache.clear()
        self.status_service._cache.clear()
        self.category_service._cache.clear()
        self.manufacturer_service._cache.clear()
        self.model_service._cache.clear()
        self.location_service._cache.clear()
        self.field_service._cache.clear()
        self.fieldset_service._cache.clear()
        self.finder._all_assets_cache = None
        
    def clear_asset_cache(self):
        print("Clearing AssetService cache...")
        self.asset_service._cache.clear()
    
    def clear_status_label_cache(self):
        print("Clearing StatusLabelService cache...")
        self.status_service._cache.clear()
    
    def clear_category_cache(self):
        print("Clearing CategoryService cache...")
        self
    
    def clear_manufacturer_cache(self):
        print("Clearing ManufacturerService cache...")
        self.manufacturer_service._cache.clear()
    
    def clear_model_cache(self):
        print("Clearing ModelService cache...")
        self.model_service._cache.clear()
    
    def clear_location_cache(self):
        print("Clearing LocationService cache...")
        self.location_service._cache.clear()

    def clear_field_cache(self):
        print("Clearing FieldService cache...")
        self.field_service._cache.clear()
        
    def clear_fieldset_cache(self):
        print("Clearing FieldsetService cache...")
        self.fieldset_service._cache.clear()
    
    
if __name__ == "__main__":
    snipe_cache_clearer = SnipeCacheClearer()
    