public class SDO_Service_Customer360_MultipleObjects {
    @AuraEnabled
    public static Contact getContact (Id recid) {
        String sObjName = recid.getSObjectType(). getDescribe().getName();
        if(sObjName == 'VoiceCall'){
            return [Select Name,SDO_Cust360_CSAT__c,SDO_Cust360_Metric1__c,SDO_Cust360_Metric2__c,SDO_Cust360_ChurnRisk__c,SDO_Cust360_Contact_Picture_URL__c,SDO_Cust360_Id__c,MailingCity,MailingState from Contact 
            where Id in (Select Contact__c from VoiceCall where Id = :recid)];
        }else if(sObjName == 'Contact'){
            return [Select Name,SDO_Cust360_CSAT__c,SDO_Cust360_Metric1__c,SDO_Cust360_Metric2__c,SDO_Cust360_ChurnRisk__c,SDO_Cust360_Contact_Picture_URL__c,SDO_Cust360_Id__c,MailingCity,MailingState From Contact Where Id = :recid];
        }else if(sObjName == 'Account'){
            return [Select Name,SDO_Cust360_CSAT__c,SDO_Cust360_Metric1__c,SDO_Cust360_Metric2__c,SDO_Cust360_ChurnRisk__c,SDO_Cust360_Contact_Picture_URL__c,SDO_Cust360_Id__c,MailingCity,MailingState From Contact Where Account.Id = :recid];
        }else if(sObjName == 'Case'){
            return [Select Name,SDO_Cust360_CSAT__c,SDO_Cust360_Metric1__c,SDO_Cust360_Metric2__c,SDO_Cust360_ChurnRisk__c,SDO_Cust360_Contact_Picture_URL__c,SDO_Cust360_Id__c,MailingCity,MailingState from Contact 
            where Id in (Select ContactId from Case where Id = :recid)];
        }else if(sObjName == 'MessagingSession'){
            return [Select Name,SDO_Cust360_CSAT__c,SDO_Cust360_Metric1__c,SDO_Cust360_Metric2__c,SDO_Cust360_ChurnRisk__c,SDO_Cust360_Contact_Picture_URL__c,SDO_Cust360_Id__c,MailingCity,MailingState from Contact 
            where Id in (Select EndUserContactId from MessagingSession where Id = :recid)];
        }
        else if(sObjName == 'LiveChatTranscript'){
            return [Select Name,SDO_Cust360_CSAT__c,SDO_Cust360_Metric1__c,SDO_Cust360_Metric2__c,SDO_Cust360_ChurnRisk__c,SDO_Cust360_Contact_Picture_URL__c,SDO_Cust360_Id__c,MailingCity,MailingState from Contact 
            where Id in (Select ContactId  from LiveChatTranscript where Id = :recid)];
        }
        else{
            return null;
        }
    }
}