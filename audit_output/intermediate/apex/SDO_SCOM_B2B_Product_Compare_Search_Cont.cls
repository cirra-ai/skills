/**
 * @description Demonstrates how to make REST calls to ConnectApi.CommerceSearch class
 * to perform Search and Category browsing for B2B Commerce on Lightning.
 *
 * @see SDO_SCOM_B2B_Product_Compare_Utils
 */
public with sharing class SDO_SCOM_B2B_Product_Compare_Search_Cont {
    /**
     * @description Demonstrates how to call ConnectApi.CommerceSearch.productSearch
     * @param communityId The Id of the community from which the call originated
     * @param searchQuery The search query parameters which includes searchTerm, categoryId, refinements, page and includePrices
     * @param @param effectiveAccountId ID of the account for which the request is made. If null, defaults to the account ID for the context user.
     */
    @AuraEnabled(cacheable=true)
    public static Object productSearch(
        String communityId,
        String searchQuery,
        String effectiveAccountId
    ) {
        String webstoreId = SDO_SCOM_B2B_Product_Compare_Utils.resolveCommunityIdToWebstoreId(
            communityId
        );

        HttpRequest httpRequest = new HttpRequest();
        Object response;
        /*
            The profile or permission set associated with the user must have these permissions enabled:

                API Enabled
                Apex REST Services
        */

        String domain = System.URL.getOrgDomainUrl().toExternalForm();

        httpRequest.setMethod('POST');
        httpRequest.setHeader(
            'Content-Type',
            'application/json;  charset=utf-8'
        );

        String restAPIURL = domain + 
        '/services/data/v' +

        '51.0' +

        '/commerce/webstores/' +
        webstoreId +
        '/search/product-search';

        if(effectiveAccountId != null) {
            restAPIURL += '?effectiveAccountId=' + effectiveAccountId;
        }
        else {
            WebStore store = null;
            List<WebStore> storeList = [Select Id, GuestBuyerProfileId from WebStore where Id = :webstoreId];

            if(storeList.size() > 0) {
                store = storeList.get(0);

                System.debug('GuestBuyerProfileId: ' + store.GuestBuyerProfileId);
            }

            if(store != null) {
                restAPIURL += '?effectiveAccountId=' + store.GuestBuyerProfileId;
            }
        }

        httpRequest.setEndpoint(
            restAPIURL
        );

        System.debug('restAPIURL: ' + restAPIURL);
        System.debug('UserInfo.getSessionId(): ' + UserInfo.getSessionId());

        httpRequest.setHeader('Authorization', 'OAuth ' + UserInfo.getSessionId());
        httpRequest.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionID());

        httpRequest.setBody(searchQuery);

        try {
            Http http = new Http();
            HttpResponse httpResponse = http.send(httpRequest);
            Integer statusCode = httpResponse.getStatusCode();

            if (statusCode >= 200 && statusCode <= 204) {
                response = JSON.deserializeUntyped(httpResponse.getBody());
            } else {
                System.debug(' httpResponse ' + httpResponse.getBody());
                throw new CalloutException(httpResponse.getBody());
            }
        } catch (System.Exception e) {
            System.debug('ERROR: ' + e);
            throw e;
        }
        return response;
    }
}