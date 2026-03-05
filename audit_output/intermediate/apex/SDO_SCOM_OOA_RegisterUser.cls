public without sharing class SDO_SCOM_OOA_RegisterUser {

    @AuraEnabled
    public static List<SDO_SCOM_OOA_Approved_Domain__c> getDomains(){
        List<SDO_SCOM_OOA_Approved_Domain__c> domainlist = [SELECT Name FROM SDO_SCOM_OOA_Approved_Domain__c];
        return domainlist;
    }

    @AuraEnabled
    public static SDO_SCOM_OOA_Commerce_User_Requests__c createRequest(string accId, string rFname, string rLname, string rEmail, string rPhone, string rRole){
        SDO_SCOM_OOA_Commerce_User_Requests__c reqObj = NEW SDO_SCOM_OOA_Commerce_User_Requests__c();
        reqObj.Account__c = accId;
        reqObj.Email__c = rEmail;
        reqObj.First_Name__c = rFname;
        reqObj.Last_Name__c = rLname;
        reqObj.phone__c = rPhone;
        reqObj.Role__c = rRole;
        reqObj.Status__c = 'Pending';

        INSERT reqObj;
        RETURN reqObj;
    }

}