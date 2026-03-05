public with sharing class Sdo_scom_product_reviews {
    public Sdo_scom_product_reviews() {}

    @AuraEnabled(cacheable=true)
    public static List<SDO_SCOM_Customer_Review__c> getCustomObjects() {
        return [
            SELECT Id, 	Username__c, Product_Review_Date__c, Product_Rating__c, Product_Review_Title__c, Product_Review_Description__c 
            FROM SDO_SCOM_Customer_Review__c 
        ];
    }
}