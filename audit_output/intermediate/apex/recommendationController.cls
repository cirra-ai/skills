public with sharing class recommendationController {
    public recommendationController() {

    }
  @AuraEnabled
    public static String getRecommendations(String recommender, String anchorValues, String storeNameValue, String cookie) {
        String baseUrl = URL.getOrgDomainUrl().toExternalForm();
        //String webstoreId = '0ZEB0000000ToYWOA0';
        WebStoreNetwork webStoreNetwork = Database.query('SELECT WebStoreId FROM WebStoreNetwork WHERE Network.UrlPathPrefix = :storeNameValue LIMIT 1');
        String webStoreId = webStoreNetwork.WebStoreId;
        System.debug('webStoreId:' + webStoreId);
        String endpoint = +baseUrl+'/services/data/v55.0/commerce/webstores/'+webStoreId+'/ai/recommendations?language=en-US&asGuest=true&recommender='+recommender;
        if (anchorValues.length() > 0) {
            endpoint += '&anchorValues='+anchorValues;
        }

        HttpRequest req = new HttpRequest();
        req.setEndpoint(endpoint);
        req.setHeader('Cookie', cookie);
        req.setMethod('GET');
        req.setHeader('Authorization', 'OAuth ' + UserInfo.getSessionId());
        Http http = new Http();
        HTTPResponse res = http.send(req);
        return res.getBody();
    }
}