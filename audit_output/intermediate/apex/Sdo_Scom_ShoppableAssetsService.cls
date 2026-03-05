public with sharing class Sdo_Scom_ShoppableAssetsService {
    private static List<SDO_SCOM_Replacement_Parts__c> getReplacementParts(Id assetId) {
        if(!Schema.sObjectType.SDO_SCOM_Replacement_Parts__c.fields.Product__c.isAccessible()) {
            String errorMeassage = 'You don\'t have access to required fileds, Please contact your admin.';
            System.debug('getReplacementParts' + errorMeassage);
            throw new AuraHandledException(errorMeassage);
        }
        return [
            Select Product__c
            From SDO_SCOM_Replacement_Parts__c
            Where Asset__c = :assetId
        ];
    }

    @AuraEnabled
    public static List<ConnectApi.ProductOverview> getShoppableAssets(Id assetId, Id webstoreId, Id effectiveAccountId) {
        System.debug('Shoppable Assets - assetId: ' + assetId);
        System.debug('Shoppable Assets - webstoreId: ' + webstoreId);
        System.debug('Shoppable Assets - effectiveAccountId: ' + effectiveAccountId);
        List<SDO_SCOM_Replacement_Parts__c> replacementParts = getReplacementParts(assetId);
        List<ConnectApi.ProductOverview> products = new List<ConnectApi.ProductOverview>();
        if(replacementParts.size() == 0) {
            System.debug('No Replacement Parts found for an asset: ' + assetId);
            return products;
        }
        List<Id> productIds = new List<Id>();
        for (SDO_SCOM_Replacement_Parts__c  replacementPart: replacementParts) {
            productIds.add(replacementPart.get('Product__c').toString());
        }
        System.debug('Shoppable Assets - Replacement parts: ' + productIds);
        try {
            ConnectApi.ProductOverviewCollection productsCollection = ConnectApi.CommerceCatalog.getProducts(webstoreId, effectiveAccountId, productIds, null, null, false);
            products = productsCollection.products;
            System.debug('Shoppable Assets - Accessible Replacement parts: ' + products);
        } catch (Exception e) {
            String errorMeassage = e.getMessage();
            System.debug('Shoppable Assets - Exception while retrieving product details: ' + errorMeassage);
            throw new AuraHandledException(errorMeassage);
        }
        return products;
    }
}