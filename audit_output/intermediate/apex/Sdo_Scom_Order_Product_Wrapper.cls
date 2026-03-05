public with sharing class Sdo_Scom_Order_Product_Wrapper{
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
	
	@AuraEnabled
	public String unitPrice{get;set;}
	
	@AuraEnabled
	public String currencyIsoCode{get;set;}
}