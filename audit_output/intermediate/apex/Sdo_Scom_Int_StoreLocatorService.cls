public interface Sdo_Scom_Int_StoreLocatorService {

    List<Sdo_Scom_LocationWrapper> fetchLocations(Integer distance, String unit, Decimal userLatitude, Decimal userLongitude);
    List<Sdo_Scom_LocationWrapper> fetchPreferredStore(Integer distance, String unit, Decimal userLatitude, Decimal userLongitude);
    void updateDefaultStore(Id storeId);
    void updateLocations();
}