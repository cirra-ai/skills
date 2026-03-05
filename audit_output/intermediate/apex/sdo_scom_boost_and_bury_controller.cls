//apex to configure boost and bury rules
public with sharing class sdo_scom_boost_and_bury_controller {
    private static final String CONTENT_TYPE_VALUE = 'application/json';
    private static final String CONTENT_TYPE_KEY = 'Content-Type';
    private static final String METHOD_GET = 'GET';
    private static final String METHOD_POST = 'POST';
    private static final String METHOD_DELETE = 'DELETE';
    private static final String BLANK = '';
    private static final String FORWORD_SLASH = '/';
    private static final String NAMED_CREDENTIALS = 'callout:Rest_API';
    private static final String API_BASE_PREFIX = '/services/data/v59.0/commerce/management/webstores/';
    private static final String API_BASE_POSTFIX = '/search/boost-bury-rules';

    //call out to rest api
    public static String callOut(String url, String methodName, String webStoreId, String requestBody){
        HTTPResponse res = null;
        HttpRequest req = new HttpRequest();
        req.setEndpoint(NAMED_CREDENTIALS  + API_BASE_PREFIX + webStoreId + API_BASE_POSTFIX + url);
        req.setMethod(methodName);
        req.setHeader(CONTENT_TYPE_KEY, CONTENT_TYPE_VALUE);

        if(String.isNotBlank(requestBody)){
            req.setBody(requestBody);
        }

        Http http = new Http();
        res = http.send(req);
        if(res.getStatusCode() != 200 && res.getStatusCode() != 201 && res.getStatusCode() != 204){
            List<Error> errorList = ((List<Error>)JSON.deserialize(res.getBody(), List<Error>.class));
            String message = '';
            for(Error error : errorList){
                message = message + ' ' + error.message;
            }
            throw new CustomException(message);
        }
        return res.getBody();
    }

    public class Error{
        public String message;
    }

    //get all rules
    @AuraEnabled
    public static String getRule(String webStoreId){
        return callOut('', METHOD_GET, webStoreId, BLANK);
    }

    //create rule
    @AuraEnabled
    public static String createRule(String webStoreId, String input){
        return callOut(BLANK, METHOD_POST, webStoreId, input);
    }

    //delete rule
    @AuraEnabled
    public static String deleteRule(String webStoreId, String ruleId){
        return callOut(FORWORD_SLASH + ruleId, METHOD_DELETE, webStoreId, BLANK);
    }

    //get all products so user can select on UI
    @AuraEnabled
    public static List<Product2> getProducts(){
        return [SELECT Id, Name, StockKeepingUnit 
                FROM Product2 
                WHERE isActive = true
                LIMIT 50000];
    }

    //get products for given rules
    @AuraEnabled
    public static List<Product2> getProductsById(List<String> productIds){
        return [SELECT Id, Name, StockKeepingUnit 
                FROM Product2 
                WHERE Id IN :productIds];
    }

    public class CustomException extends Exception {}
}