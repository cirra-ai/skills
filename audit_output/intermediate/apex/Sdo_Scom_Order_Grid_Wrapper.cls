public with sharing class Sdo_Scom_Order_Grid_Wrapper{
    @AuraEnabled
    public List<Sdo_Scom_Order_Product_Wrapper> orderProducts{get;set;}

    @AuraEnabled
    public String webstoreId{get;set;}
}