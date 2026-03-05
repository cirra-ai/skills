public class AIAgentMonitorController {

    @AuraEnabled
    public static String getCurrentUserFirstName() {
        return UserInfo.getFirstName();
    }

    @AuraEnabled
    public static AI_Agent_Conversation__c getConversationDetails(String conversationId){
        System.debug('Conversation Id is ' + conversationId);
         return [
            SELECT  AI_Agent_Name__c, Contact_Name__c, Conversation_Start__c, Newest_Message_Date__c, Summary__c, Flag__c, Flag_Reason__c, Conversation_Start_Seconds__c, Conversation_Summary__c, Conversation_Summary_Issue__c
            FROM    AI_Agent_Conversation__c 
            WHERE   Id  =: conversationId 
        ];
    }
    
    @AuraEnabled
    public static List<AI_Agent_Conversation_Entry__c> getConversationEntries(String conversationId){
        System.debug('Conversation Id is ' + conversationId);
         return [
            SELECT  Name, Entry_Time__c , Type__c, Transcript__c, Spoken_By__c, Translation__c
            FROM    AI_Agent_Conversation_Entry__c 
            WHERE   AI_Agent_Conversation__c  =: conversationId AND IsDemoResponse__c = false
            ORDER BY Entry_Time__c ASC
        ];
    }
    
    @AuraEnabled
    public static List<AI_Agent_Conversation_Entry__c> getDemoConversationEntries(String conversationId){
        System.debug('Conversation Id is ' + conversationId);
         return [
            SELECT  Name, Entry_Time__c , Type__c, Transcript__c, Spoken_By__c, Translation__c
            FROM    AI_Agent_Conversation_Entry__c 
            WHERE   AI_Agent_Conversation__c  =: conversationId AND IsDemoResponse__c = true
            ORDER BY Entry_Time__c ASC
        ];
    }
    
    @AuraEnabled
    public static String getCurrentUserLocale() {
        return UserInfo.getLocale();
    }
}