public class Sdo_Scom_LocationWrapper{

    @AuraEnabled
    public String VisitorAddressId{get;set;}
    @AuraEnabled
    public String LocationType{get;set;}
    @AuraEnabled
    public String Id{get;set;}
    @AuraEnabled
    public String Name{get;set;}
    @AuraEnabled
    public String Timings{get;set;}
    @AuraEnabled
    public String Services{get;set;}
    @AuraEnabled
    public String Facilities{get;set;}
    @AuraEnabled
    public Decimal Distance{get;set;}
    @AuraEnabled
    public List<Schema.Address> Addresses{get;set;}
    @AuraEnabled
    public String Phone{get;set;}
    @AuraEnabled
    public Boolean isDefault{get;set;}
    
}