public with sharing class Sdo_Scom_Cart_Summary_Wrapper{
    @AuraEnabled
    public String cartId{get;set;}

    @AuraEnabled
    public String currencyIsoCode{get;set;}

    @AuraEnabled
    public String totalPrice{get;set;}

    @AuraEnabled
    public String totalAmount{get;set;}

    @AuraEnabled
    public List<Sdo_Scom_Cart_Product_Wrapper> cartItems{get;set;}
}