public class SDO_Service_ConversationToolkitNBA {
    @AuraEnabled
    public static List<SDO_Service_Conversation_Helper__c> getConversationHelperList(){
        return [SELECT ID,Value__c, Recommended_Action__c, Agent__c, Customer__c FROM SDO_Service_Conversation_Helper__c WHERE Active__c = true];        
    }   
}