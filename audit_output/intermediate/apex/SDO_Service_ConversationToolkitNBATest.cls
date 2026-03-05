@isTest
private class SDO_Service_ConversationToolkitNBATest {
    static testMethod void SDO_Service_ConversationToolkitNBATest() {
        SDO_Service_Conversation_Helper__c chInput = new SDO_Service_Conversation_Helper__c();
        chInput.Value__c = 'TestValue';
        chInput.Active__c = true;
        insert chInput;
        List<SDO_Service_Conversation_Helper__c> conversationList = SDO_Service_ConversationToolkitNBA.getConversationHelperList();
        System.assertNotEquals(0, conversationList.size());
    }
}