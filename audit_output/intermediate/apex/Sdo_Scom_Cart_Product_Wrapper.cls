public with sharing class Sdo_Scom_Cart_Product_Wrapper{
    @AuraEnabled
    public String productId{get;set;}

    @AuraEnabled
    public Integer quantity{get;set;}

    @AuraEnabled
    public String errorMessage{get;set;}

    @AuraEnabled
    public String requestStatus{get;set;}
}