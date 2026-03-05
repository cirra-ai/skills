@isTest
public class SDO_WorkTypeMappingTest {
    
 static testMethod void testUpdateRecordType() {
        // Query Dynamic Record Types
        RecordType rt = [SELECT Id, Name FROM RecordType WHERE SobjectType = 'FSL__Work_Rule__c' AND Name != 'Field Service - Capacity Limit' LIMIT 1];

        // Query Static Record Type
        RecordType rtStatic = [SELECT Id, Name FROM RecordType WHERE SobjectType = 'FSL__Work_Rule__c' AND Name = 'Field Service - Capacity Limit' LIMIT 1];
        
        // Create test FSL__Work_Rule__c records with different Record_Type__c values
        FSL__Work_Rule__c workRule1 = new FSL__Work_Rule__c(
            Name = 'Test Work Rule 1',
            Record_Type__c = 'Field Service - Capacity Limit',
            External_Id__c = '123',
            RecordTypeId = rt.id
        );
        insert workRule1;
        
        FSL__Work_Rule__c workRule2 = new FSL__Work_Rule__c(
            Name = 'Test Work Rule 2',
            Record_Type__c = rt.Name,
            External_Id__c = '456',
            RecordTypeId = rt.id
        );
        insert workRule2;
        
        // Update the Record_Type__c value on the second record
        workRule2.Record_Type__c = 'Field Service - Capacity Limit';
        update workRule2;
        
        // Query for the updated FSL__Work_Rule__c records
        List<FSL__Work_Rule__c> updatedRecords = [
            SELECT Id, Record_Type__c, RecordTypeId 
            FROM FSL__Work_Rule__c 
            WHERE External_Id__c IN ('123', '456')
        ];
        
        // Verify that the Record_Type__c value was updated correctly
        System.assertEquals('Field Service - Capacity Limit', updatedRecords[0].Record_Type__c);
        System.assertEquals(rtStatic.Id, updatedRecords[0].RecordTypeId);
        System.assertEquals('Field Service - Capacity Limit', updatedRecords[1].Record_Type__c);
        System.assertEquals(rtStatic.Id, updatedRecords[1].RecordTypeId);
    }
}