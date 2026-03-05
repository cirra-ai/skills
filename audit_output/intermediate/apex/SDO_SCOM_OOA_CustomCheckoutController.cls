public without sharing class SDO_SCOM_OOA_CustomCheckoutController {

    @AuraEnabled(cacheable=true)
    public static User getCurrentUserDetails(String userId){
        User currentUser = [Select Id, Name, ContactId, Contact.Account.Name, Contact.SDO_SCOM_OOA_Access__c, Contact.SDO_SCOM_OOA_Approver__c, Contact.SDO_SCOM_OOA_Budget_Limit__c from User where Id =: userId];
        return currentUser;
    }

    @AuraEnabled
    public static WebCart getCartApprovalStatus(String cartId){
        WebCart currentCart = [Select Id, Name, SDO_SCOM_OOA_Credit_Override_Status__c, SDO_SCOM_OOA_Products_Override_Status__c from WebCart where Id =: cartId];
        return currentCart;
    }

    @AuraEnabled
    public static boolean requestOverride(String cartId, String approverId, String accountName, Decimal cartValue, Boolean isBudgetExceded, Boolean hasProductExceptions, String productExceptions, String orgAdminApproverId){
        try {
            if(isBudgetExceded == true){
                User approverUser = [Select Id, Name from User where ContactId =: approverId limit 1];
                SDO_SCOM_OOA_Commerce_Approval_Requests__c budgetApprovalRequest = new SDO_SCOM_OOA_Commerce_Approval_Requests__c();
                budgetApprovalRequest.Requester__c = UserInfo.getUserId();
                budgetApprovalRequest.Cart__c = cartId;
                budgetApprovalRequest.OwnerId = approverUser.Id;
                budgetApprovalRequest.Credit_Override_Amount__c = cartValue;
                budgetApprovalRequest.Type__c = 'Credit Override';
                insert budgetApprovalRequest;
            } 

            if(hasProductExceptions == true){
                SDO_SCOM_OOA_Commerce_Approval_Requests__c prodQtyRequest = new SDO_SCOM_OOA_Commerce_Approval_Requests__c();
                prodQtyRequest.Requester__c = UserInfo.getUserId();
                prodQtyRequest.Cart__c = cartId;
                prodQtyRequest.OwnerId = orgAdminApproverId;
                prodQtyRequest.Products_Quantities__c = productExceptions;
                prodQtyRequest.Type__c = 'Product/Quantity';
                insert prodQtyRequest;
                
                List<CustomNotificationType > notificationTemplate = [SELECT Id, DeveloperName FROM CustomNotificationType WHERE DeveloperName = 'SDO_SCOM_OOA_Commerce_Approval_Request_Notifications'];
                Messaging.CustomNotification currentNotification = new Messaging.CustomNotification();
                currentNotification.setNotificationTypeId(notificationTemplate[0].Id);
                currentNotification.setTitle('Product/Quantity Approval Request for ' + accountName);
                currentNotification.setBody('Submitted by ' + UserInfo.getName());
                currentNotification.setTargetId(prodQtyRequest.Id);
                currentNotification.send(new Set<String>{orgAdminApproverId});
            }

            return true;
        } catch(exception e){
            system.debug('exception ' + e.getMessage());
            AuraHandledException exp = new AuraHandledException(e.getMessage());
            exp.setMessage(e.getMessage());
            throw exp;
        }
    }

}