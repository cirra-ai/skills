public class SDO_Service_ChangeTabLabelController {
    
    @AuraEnabled 
    public static String getNewLabel(String recordId){
        String tabLabel, contactId, accountId;

        if (recordId.startsWith('570')) { // Chat Transcripts
            LiveChatTranscript ct = [SELECT ID, Name, ContactId, AccountId from LiveChatTranscript where ID = :recordId LIMIT 1];
            contactId = ct.ContactId;
            accountId = ct.AccountId;
        } else if (recordId.startsWith('0Mw')) { // Messaging Sessions
            MessagingSession ms = [SELECT ID, Name, EndUserContactId, EndUserAccountId from MessagingSession where ID = :recordId LIMIT 1];
            contactId = ms.EndUserContactId;
            accountId = ms.EndUserAccountId;
        } else if (recordId.startsWith('500')) { // Cases
            Case theCase = [SELECT ID, Subject, CaseNumber, ContactId, AccountId  From Case where ID = :recordId LIMIT 1];   
            contactId = theCase.ContactId;
            accountId = theCase.AccountId; 
        }
        else if (recordId.startsWith('0WO')) {  // Work Orders
            WorkOrder wo = [SELECT ID, SUBJECT, ContactId, AccountId From WorkOrder where ID = :recordId LIMIT 1];   
            contactId = wo.ContactId;
            accountId = wo.AccountId;   
        } else if (recordId.startsWith('0LQ')) { // Voice Calls
            // Uncomment these 2 lines and update the 'design' file on the 'SDO_Service_ChangeTabLabel' component to include 'VoiceCall' alongside the other supported objects
            //VoiceCall call = [SELECT ID,Contact__c FROM VoiceCall where ID = :recordId LIMIT 1];
            //contactId = call.Contact__c;  // Updated for SDO where we use a custom Contact field. 
        }
        
        // Now create the string to return
        if (contactId != null) {
            // Return the contact name as a priority.
            Contact con = [SELECT ID, FirstName, LastName FROM CONTACT WHERE ID = :contactId];
            tabLabel = con.FirstName + ' ' + con.LastName;
        } else if (accountId != null) {
            // Return the account name if there was no contact.
            Account a = [SELECT ID, Name FROM Account WHERE ID = :accountId];
            tabLabel = a.Name;
        }
        
        return tabLabel;
    }
}