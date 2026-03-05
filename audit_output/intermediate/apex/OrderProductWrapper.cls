/*
==========================================
    Title: OrderProductWrapper
    Purpose: Wrapper class to store order
        products.
    Author: Clay Phillips
    Date: 08/20/2020 
==========================================
*/

public with sharing class OrderProductWrapper{
    @AuraEnabled
    public String Id{get;set;}

    @AuraEnabled
    public String orderId{get;set;}

    @AuraEnabled
    public Datetime orderedDate{get;set;}

    @AuraEnabled
    public String productId{get;set;}

    @AuraEnabled
    public String productName{get;set;}

    @AuraEnabled
    public String productSKU{get;set;}

    @AuraEnabled
    public Decimal quantity{get;set;}

    @AuraEnabled
    public String productImageURL{get;set;}

    @AuraEnabled
    public String attributeDeveloperName{get;set;}

    @AuraEnabled
    public Map<String, String> attributeMap{get;set;}

    @AuraEnabled
    public Map<String,ConnectApi.ProductAttributeSetInfo> attributeSetInfo{get;set;}
}