public without sharing class SDO_SCOM_OOA_Utility {
    
    @AuraEnabled(cacheable=true)
    public static List<SDO_SCOM_OOA_Commerce_Approval_Requests__c> getCurrentUserApprovals() {
        return [
            Select Id, Name, OwnerId, Budget_Limit__c, Credit_Override_Amount__c, Status__c, Requester__r.Name, Requester__r.FirstName, Requester__r.LastName
            FROM SDO_SCOM_OOA_Commerce_Approval_Requests__c
            WHERE OwnerId =: userInfo.getUserId()
            ORDER BY CreatedDate DESC
        ];
    }
    
    @AuraEnabled(cacheable=true)
    public static List<NetworkMember> getCurrentCommunityUsersInfoForCompany(){
        try {
            Id currentUserAccountId = [SELECT AccountId FROM User WHERE Id =: UserInfo.getUserId()].AccountId;
            List<NetworkMember> currentCommunityUsersForCompany = [Select Id, Member.Name, Member.FirstName, Member.LastName, Member.AccountId, Network.Name, Member.Contact.SDO_SCOM_OOA_Access__c, Member.Contact.SDO_SCOM_OOA_Budget_Limit__c, Member.Contact.SDO_SCOM_OOA_Approver__c, Member.Contact.SDO_SCOM_OOA_Approver__r.Name
                                                                   FROM NetworkMember 
                                                                   WHERE NetworkId =: Network.getNetworkId() AND Member.AccountId =: currentUserAccountId AND MemberId !=: UserInfo.getUserId()];
            return currentCommunityUsersForCompany;
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
    
    @InvocableMethod(label='Update SCOM OOA Commerce Approval Request Status To Cart' description='Updates commerce approval request status on the related cart record')
    public static void updateApprovalStatus(List<SDO_SCOM_OOA_Commerce_Approval_Requests__c> approvalRecords){
        List<Id> cartRecordIds = new List<Id>();
        for(SDO_SCOM_OOA_Commerce_Approval_Requests__c apr: approvalRecords){
            cartRecordIds.add(apr.Cart__c);
        }
        
        Map<ID, WebCart> cartRecordMap = new Map<ID, WebCart>([SELECT Id, Name, SDO_SCOM_OOA_Credit_Override_Status__c, SDO_SCOM_OOA_Products_Override_Status__c FROM WebCart WHERE Id IN :cartRecordIds]);
        
        for(SDO_SCOM_OOA_Commerce_Approval_Requests__c apr: approvalRecords){
            WebCart cartRec = cartRecordMap.get(apr.Cart__c);
            
            if(apr.Type__c == 'Credit Override'){
                cartRec.SDO_SCOM_OOA_Credit_Override_Status__c = apr.Status__c;
            }
            
            if(apr.Type__c == 'Product/Quantity'){
                cartRec.SDO_SCOM_OOA_Products_Override_Status__c = apr.Status__c;
            }
            
            cartRecordMap.put(apr.Cart__c, cartRec);
        }
        
        List<WebCart> cartRecsToUpdate = cartRecordMap.values();
        if(cartRecsToUpdate.size() > 0){
            UPDATE cartRecsToUpdate;
        }     
    }
}