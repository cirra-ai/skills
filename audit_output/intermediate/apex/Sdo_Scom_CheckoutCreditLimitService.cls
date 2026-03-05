public without sharing class Sdo_Scom_CheckoutCreditLimitService {
    @AuraEnabled
    public static BuyerAccount getAvailableCreditLimit(String effectiveAccountId) {
        try {
            // Converting Id to 18 chars
            Id buyerId = effectiveAccountId;
            List<BuyerAccount> buyerAccounts = [SELECT BuyerId, AvailableCredit, Name FROM BuyerAccount WHERE BuyerId = :buyerId];
            if(buyerAccounts.isEmpty()) {
                System.debug('No Buyer Accounts are associated with ' + effectiveAccountId + ' account.');
                String accountNotfoundError = 'Your account is not a Buyer Account! Please choose payment other than Purchare Order or contact your system admin.';
                AuraHandledException e = new AuraHandledException(accountNotfoundError);
                e.setMessage(accountNotfoundError);
                throw e;
            }
            return buyerAccounts.get(0);
        } catch(Exception ex) {
            System.debug(ex.getMessage());
            AuraHandledException e = new AuraHandledException(ex.getMessage());
            e.setMessage(ex.getMessage());
            throw e;
        }
    }
}