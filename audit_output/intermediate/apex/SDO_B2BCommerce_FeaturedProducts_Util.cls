public with sharing class SDO_B2BCommerce_FeaturedProducts_Util {
    
    public class ProductDetailWrapper {

        public String id {get; set;}
        public String name {get; set;}

        public ConnectApi.ProductMedia defaultImage {get; set;}
        public ConnectApi.ProductEntitlement entitlement {get; set;}
        public Map<String, Object> fields {get; set;}
        public List<ConnectApi.ProductMediaGroup> mediaGroups {get; set;}
        public ConnectApi.ProductCategoryPath primaryProductCategoryPath {get; set;}

        public ProductPricingWrapper prices {get; set;}

        public Integer sequence {get; set;}
    }

    Public class ProductPricingWrapper {

        public String listPrice {get; set;}
        public String unitPrice {get; set;}

        public String pricebookEntryId {get; set;}

    }

    public static void addMessage(Message msg, Integer pos, Map<String, Object> responseMap) {

        List<SDO_B2BCommerce_FeaturedProducts_Util.Message> retMessages = null;

        if(responseMap.containsKey('messages')) {
            retMessages = (List<SDO_B2BCommerce_FeaturedProducts_Util.Message>)responseMap.get('messages');
        }
        else {
            retMessages = new List<SDO_B2BCommerce_FeaturedProducts_Util.Message>();
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