public with sharing class SDO_SFS_AAController {
     //get the asset id from the work order
     @AuraEnabled(cacheable=true)
     public static String getAssetId(String workOrderId){
         String assetId = '';
         if(workOrderId != null) {
                     assetId = [SELECT AssetId FROM WorkOrder WHERE Id =: workOrderId LIMIT 1].AssetId;
         }
         return assetId;
     }    
     //get the asset attributes for the asset, including the name, value and datatype
     @AuraEnabled(cacheable=true)
     public static list<AAwithPicklistValues> getAssetAttributes(String assetId,String workOrderId){    
         list<AssetAttribute> assetAttributes = new list<AssetAttribute>();
         if(assetId != null) {
                     assetAttributes = [
                         SELECT 
                         AttributeName,
                         AttributeValue,
                         Id,
                         AttributeDefinition.DataType,
                         AttributeDefinition.IsRequired,
                         AttributeDefinition.UnitofMeasure.UnitCode
                     FROM AssetAttribute WHERE AssetId =: assetId];
         }
         WorkOrder thisWO = [select id, workordernumber from workorder where id =: workOrderId limit 1];
         Asset thisAsset = [select id, name from asset where id =: assetId limit 1];
         list<AAwithPicklistValues> listAAPLV = new list<AAwithPicklistValues>();
         For(AssetAttribute aa : assetAttributes) {
             list<PickListValue> listPLV = new list<PickListValue>();
             If(aa.AttributeDefinition.DataType=='Picklist'){
                 For(AttributePicklistValue apv : getAttributePickList(aa.Id)) {
                     PickListValue plv = new PickListValue();
                     plv.Id = apv.Id;
                     plv.DisplayValue = apv.DisplayValue;
                     listPLV.add(plv);
                 }
             }
             AAwithPicklistValues thisAAPLV = new AAwithPicklistValues();
             thisAAPLV.WorkOrderNumber = thisWO.WorkOrderNumber;
             thisAAPLV.AssetName = thisAsset.Name;
             thisAAPLV.AttributeName = aa.AttributeName;
             thisAAPLV.AttributeValue = aa.AttributeValue;
             thisAAPLV.Id = aa.Id;
             thisAAPLV.DataType = aa.AttributeDefinition.DataType;
             thisAAPLV.IsRequired = aa.AttributeDefinition.IsRequired;
             thisAAPLV.UnitOfMeasure = aa.AttributeDefinition.UnitofMeasure.UnitCode;
             thisAAPLV.listPLV = listPLV;
             listAAPLV.add(thisAAPLV);
             }
         return listAAPLV;
     }
     //get the picklist options for attributes of type picklist
     @AuraEnabled(cacheable=true)
     public static list<AttributePicklistValue> getAttributePickList(String attributeId){    
         list<AttributePicklistValue> attributePickListOptions = new list<AttributePicklistValue>();
         if(attributeId != null) {
         String adPicklistId = [select attributedefinition.PicklistId from assetattribute where id = :attributeId limit 1].attributedefinition.PicklistId;
             attributePickListOptions = [
                         SELECT 
                         DisplayValue,
                         Value,
                         Id
                     // FROM AttributePicklistValue WHERE PickListId in (select PicklistId from AttributeDefinition where Id =: attributeId)];
                     FROM AttributePicklistValue WHERE PickListId =: adPicklistId];
         }
         return attributePickListOptions;
     }
     //update the asset attribute with the provided value - async needed at this point since this object seems more like a platform event
     @AuraEnabled
     public static void saveAttribute(String attributeId, String attributeValue){
         AssetAttribute assetAttribute = [select Id,AttributeValue,AttributeDefinitionId from AssetAttribute where Id =: attributeId limit 1];
         String assetDataType = [select DataType from AttributeDefinition where id =: assetAttribute.AttributeDefinitionId limit 1].DataType;
         // picklists data types are updated by setting AttributePicklistValueId. Other data types update AttributeValue
         if(assetDataType == 'Picklist') 
             assetAttribute.AttributePicklistValueId = attributeValue;
         else 
             assetAttribute.AttributeValue = attributeValue;
         database.updateImmediate (assetAttribute);
     }
     public class PickListValue{
         @AuraEnabled Public string Id;
         @AuraEnabled Public string DisplayValue;
     }
 
     public class AAwithPicklistValues{
         @AuraEnabled Public String WorkOrderNumber;
         @AuraEnabled Public String AssetName;
         @AuraEnabled Public String AttributeName;
         @AuraEnabled Public String AttributeValue;
         @AuraEnabled Public String Id;
         @AuraEnabled Public String DataType;
         @AuraEnabled Public Boolean IsRequired;
         @AuraEnabled Public String UnitOfMeasure;
         @AuraEnabled Public list<PickListValue> listPLV;
     }
}