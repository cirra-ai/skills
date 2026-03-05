public with sharing class SDO_SCOM_contactListB2B {
    @AuraEnabled(cacheable=true)
    public static List<Contact> getContactList() {
        return [SELECT Id, Name, Title, AccountId, MobilePhone, LastViewedDate, Email FROM Contact ORDER BY LastViewedDate DESC NULLS LAST LIMIT 12];
    }
}