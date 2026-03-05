public with sharing class Sdo_Scom_Auction_RegisterPricingService {
    private static String APEX_CLASS_NAME = 'Sdo_Scom_Auction_PricingService';

    private static ApexClass getApexClass(String apexClassname) {
        return [
            SELECT Id
            FROM ApexClass
            WHERE Name = :apexClassname
            LIMIT 1
        ];
    }

    private static RegisteredExternalService getRegisteredExternalService(Id apexClassId) {
        return [
            SELECT Id
            FROM RegisteredExternalService
            WHERE ExternalServiceProviderType='ApexClass' AND ExternalServiceProviderId = :apexClassId LIMIT 1
        ];
    }

    
    public static void register() {
        try {
            // Get apex Class Id
            ApexClass apexClass = getApexClass(APEX_CLASS_NAME);

            // RegisteredExternalService insert values
            RegisteredExternalService pricingServiceExtension = new RegisteredExternalService();
            pricingServiceExtension.language = 'en_US';
            pricingServiceExtension.developerName = APEX_CLASS_NAME;
            pricingServiceExtension.extensionPointName = 'Commerce_Domain_Pricing_Service';
            pricingServiceExtension.externalServiceProviderType = 'Extension';
            pricingServiceExtension.externalServiceProviderId = apexClass.Id;
            pricingServiceExtension.masterLabel = APEX_CLASS_NAME;
            insert pricingServiceExtension;
            System.debug('Sdo_Scom_Auction_PricingService registered successful: ' + pricingServiceExtension);
        } catch(Exception e) {
            System.debug('An exception occurred during Sdo_Scom_Auction_PricingService register: ' + e.getMessage());
        }
    }

    public static void deRegister() {
        try {
            // Get apex Class Id
            ApexClass apexClass = getApexClass(APEX_CLASS_NAME);

            RegisteredExternalService pricingServiceExtension = getRegisteredExternalService(apexClass.Id);
            if(pricingServiceExtension != null) {
                delete pricingServiceExtension;
                System.debug('Sdo_Scom_Auction_PricingService de-registered successful: ' + pricingServiceExtension);
            }
        } catch(Exception e) {
            System.debug('An exception occurred during Sdo_Scom_Auction_PricingService de-register: ' + e.getMessage());
        }
    }
}