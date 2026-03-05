public with sharing class SFS_DocBuilderMgr {

    @AuraEnabled(cacheable=true)
    public static List<WorkPlan> getRelatedWorkSteps(Id woId) {
        if(String.valueof(woId).startsWith ('08p'))
        {
            return [SELECT Id,Name,(SELECT Id,Name,Status,Description from WorkSteps ORDER BY ExecutionOrder ASC) from WorkPlan where WorkOrderId IN (SELECT ParentRecordId from ServiceAppointment where Id=:woId)];
        }
        return [SELECT Id,Name,(SELECT Id,Name,Status,Description from WorkSteps ORDER BY ExecutionOrder ASC) from WorkPlan where WorkOrderId=:woId or WorkOrderLineItemId=:woId WITH SECURITY_ENFORCED ORDER BY ExecutionOrder ASC];
       
    }
    
    @AuraEnabled(cacheable=true)
    public static List<WorkOrderLineItem> getWolis(Id workOrderId)
    {
        if(String.valueof(workOrderId).startsWith ('08p'))
        {
             return [SELECT Id, Subject, (SELECT Id,Product2.Name,QuantityConsumed,QuantityUnitOfMeasure from ProductsConsumed) FROM WorkOrderLineItem WHERE WorkOrderId IN (SELECT ParentRecordId from ServiceAppointment where Id=:workOrderId) WITH SECURITY_ENFORCED ORDER BY CreatedDate ASC];
        }
        return [SELECT Id, Subject, (SELECT Id,Product2.Name,QuantityConsumed,QuantityUnitOfMeasure from ProductsConsumed) FROM WorkOrderLineItem WHERE WorkOrderId=:workOrderId WITH SECURITY_ENFORCED ORDER BY CreatedDate ASC];
    }
     @AuraEnabled(cacheable=true)
     public static Map<ID, String> getRelatedFilesByRecordId(String recordId)
     {
            List<ContentDocumentLink> files = [SELECT ContentDocumentId FROM ContentDocumentLink WHERE LinkedEntityId = :recordId];
            List<ID> fileIDs = new List<ID>();
            for (ContentDocumentLink docLink : files) {
                fileIDs.add(docLink.ContentDocumentId);
            }
     
            List<ContentVersion> docs = [SELECT ContentDocumentId, FileExtension, Title 
                FROM ContentVersion WHERE ContentDocumentId IN : fileIDs];
            Map<ID, String> mapIdTitle = new Map<ID, String>();
            for (ContentVersion docLink : docs) {
                mapIdTitle.put(docLink.ContentDocumentId, docLink.Title);
            }
            return mapIdTitle;      
     }
     
   
}