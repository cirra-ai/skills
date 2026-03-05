public with sharing class SDO_B2B_Cart_CustomValidation {

    @AuraEnabled
    public static Map<String, String> fetchInitValues(String communityId, String effectiveAccountId, String cartId) {

        System.debug('begin fetchInitValues()');

        System.debug('communityId: ' + communityId);
        System.debug('effectiveAccountId: ' + effectiveAccountId);
        System.debug('cartId: ' + cartId);

        Map<String, String> responseMap = new Map<String, String>();
        
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);

        responseMap.put('webstoreId', webstoreId);

        //responseMap.put('effectiveAccountId', effectiveAccountId);

        if(cartId == null && effectiveAccountId != '000000000000000') {
            ConnectApi.CartSummary cs = null;
            if(Test.isRunningTest() == false) {
                cs = ConnectApi.CommerceCart.getOrCreateActiveCartSummary(webstoreId, effectiveAccountId, 'active');
            }
            else {
                cs = new ConnectApi.CartSummary();
                cs.cartId = cartId;
                cs.accountId = effectiveAccountId;
            }

            System.debug('cs: ' + cs);

            responseMap.put('cartId', cs.cartId);

            responseMap.put('effectiveAccountId', cs.accountId);
        }
        else {
            responseMap.put('cartId', cartId);
            responseMap.put('effectiveAccountId', effectiveAccountId);
        }

        return responseMap;

    }

    /*
        This method is used to convert the community Id to the web store Id.
    */

    @AuraEnabled
    public static String resolveCommunityIdToWebstoreId(String communityId) {
        if(communityId == null || communityId == '') {
            return null;
        }
        
        String webstoreId = null;

        List<WebStoreNetwork> wsnList = [SELECT WebStoreId FROM WebStoreNetwork WHERE NetworkId = :communityId];

        if(wsnList.size() > 0) {
            WebStoreNetwork wsn = wsnList.get(0);
            webstoreId = wsn.WebStoreId;
        }

        return webstoreId;
    }
    
    @AuraEnabled
    public static Map<String, Object> fetchCustomCartValidation(String cartId){

        System.debug('cartId: ' + cartId);

        Map<String, Object> responseMap = new Map<String, Object>();

        List<Message> retMessages = new List<Message>();
        responseMap.put('messages', retMessages);

        responseMap.put('customMessageType', null);
        responseMap.put('customMessageText', null);
        responseMap.put('errorMsg', null);

        try {
            List<WebCart> cartList = [Select Id, Status, Type, Custom_Message_Type__c, Custom_Message_Text__c from WebCart where Id = :cartId];

            System.debug('cartList: ' + cartList);

            if(cartList.size() > 0) {
                WebCart cart = cartList.get(0);

                responseMap.put('customMessageType', cart.Custom_Message_Type__c);
                responseMap.put('customMessageText', cart.Custom_Message_Text__c);
            }
        } catch (Exception e) {
            addMessage(new Message('Error', e.getMessage(), ERROR, true), 0, responseMap);
        }

        retMessages = (List<Message>)responseMap.get('messages');

        String messagesJson = JSON.serialize(retMessages);
        System.debug('messagesJson: ' + messagesJson);
        responseMap.put('messagesJson', messagesJson);

        System.debug('responseMap: ' + responseMap);

        return responseMap;
    }

    public static void addMessage(Message msg, Integer pos, Map<String, Object> responseMap) {

        List<Message> retMessages = null;

        if(responseMap.containsKey('messages')) {
            retMessages = (List<Message>)responseMap.get('messages');
        }
        else {
            retMessages = new List<Message>();
        }

        if(pos == null) {
            retMessages.add(msg);
        }
        else if(retMessages.size() <= 0) {
            retMessages.add(msg);
        }
        else {
            retMessages.add(pos, msg);
        }

        responseMap.put('messages', retMessages);

    }    

    public static final String ERROR = 'error';
    public static final String INFO = 'info';
    public static final String SUCCESS = 'success';
    public static final String WARN = 'warn';

    public class Message {

        public String severity {get; set;}
        public String title {get; set;} 
        public String message {get; set;}
        public Boolean toast {get; set;}

        public Message() {
            toast = true;
        }

        public Message(String title, String message, String severity) {
            this();
            this.title = title;
            this.message = message;
            this.severity = severity;
        }

        public Message(String title, String message, String severity, Boolean toast) {
            this();
            this.title = title;
            this.message = message;
            this.severity = severity;
            this.toast = toast;
        }

    }

}