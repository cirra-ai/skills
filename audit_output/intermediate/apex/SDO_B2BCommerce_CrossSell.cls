/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */

 public with sharing class SDO_B2BCommerce_CrossSell {

  @AuraEnabled(cacheable=true)
  public static List<ConnectApi.ProductDetail> getCrossSellProducts(
    String communityId,
    String productID,
    String effectiveAccountID,
    String productType
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreID = resolveCommunityIdToWebstoreId(communityId);
    System.Debug('****** webstoreID -' + webstoreID);
    System.Debug('****** productID -' + productID);
    System.Debug('****** effectiveAccountID -' + effectiveAccountID);

    //New list to received products details
    List<ConnectApi.ProductDetail> myProductsInformations = new List<ConnectApi.ProductDetail>();

    List<Cross_Sell_Recommendations__c> myProductsID = new List<Cross_Sell_Recommendations__c>();

    if(Schema.sObjectType.Cross_Sell_Recommendations__c.fields.Recommended_Product__c.isAccessible()
        && Schema.sObjectType.Cross_Sell_Recommendations__c.fields.Recommended_Product_Parent__c.isAccessible()
        && Schema.sObjectType.Cross_Sell_Recommendations__c.fields.Product_Type__c.isAccessible()
        && Schema.sObjectType.Cross_Sell_Recommendations__c.fields.Sequence__c.isAccessible()) {

        // Need Sharing Setting for external user on this object
        if(productType == null || productType == '') {
          myProductsID = [
            SELECT Recommended_Product__c
            FROM Cross_Sell_Recommendations__c
            WHERE Recommended_Product_Parent__c = :productID
            ORDER BY Sequence__c ASC
          ];
        }
        else {
          myProductsID = [
            SELECT Recommended_Product__c
            FROM Cross_Sell_Recommendations__c
            WHERE Recommended_Product_Parent__c = :productID
            AND Product_Type__c = :productType
            ORDER BY Sequence__c ASC
          ];
        }

    }
    
    System.debug('myProductsID.size = ' + myProductsID.size());

    Integer count = 0;
    
    for (Cross_Sell_Recommendations__c myRelatedProductId : myProductsID) {

        ConnectApi.ProductDetail myproduct = null;

        try {
            myproduct = SDO_B2BCommerce_CrossSell.getProduct(
                webstoreID,
                myRelatedProductId.Recommended_Product__c,
                effectiveAccountID
            );
        }
        catch(Exception e) {
            System.debug('Exception: ' + e.getMessage());
            System.debug('Line #: ' + e.getLineNumber());
            System.debug(e.getStackTraceString());
        }

        if(myproduct != null){
            myProductsInformations.add(myproduct);
        }

        count++;
    }
    
    System.Debug('****** BACK TO HOME ##### -' + myProductsInformations);
    return myProductsInformations;
  }

  @AuraEnabled(cacheable=true)
  public static ConnectApi.ProductDetail getProduct(
    String webstoreId,
    String productId,
    String effectiveAccountId
  ) {

    ConnectApi.ProductDetail pd = null;

    if(Test.isRunningTest() == false) {
      pd = ConnectApi.CommerceCatalog.getProduct(webstoreId, productId, effectiveAccountID, null, false, null, false, true, false);
    }
    else {
    }

    return pd;
  }

  // Function to retrieve Product Price
  @AuraEnabled(cacheable=true)
  public static ConnectApi.ProductPrice getProductPrice(
    String communityId,
    String productId,
    String effectiveAccountId
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreId = resolveCommunityIdToWebstoreId(communityId);
    
    System.debug('productId: ' + productId);

    ConnectApi.ProductPrice price = null;

    if(Test.isRunningTest() == false) {
      try{
        price = ConnectApi.CommerceStorePricing.getProductPrice(webstoreId, productId, effectiveAccountId );
      }
      catch(Exception e){
        System.debug('Exception: ' + e.getMessage());
        System.debug('Line #: ' + e.getLineNumber());
        System.debug(e.getStackTraceString());
      }
    }
    else {
    }

    return price;
  }

  @AuraEnabled
  public static ConnectApi.CartItem addToCart(
    String communityId,
    String productId,
    String quantity,
    String effectiveAccountId
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreId = resolveCommunityIdToWebstoreId(communityId);

    System.debug('communityId: ' + communityId);
    System.debug('productId: ' + productId);
    System.debug('quantity: ' + quantity);
    System.debug('effectiveAccountId: ' + effectiveAccountId);
    System.debug('webstoreId: ' + webstoreId);

    ConnectApi.CartItemInput cartInput = new ConnectApi.CartItemInput();
    cartInput.productId = productId;
    cartInput.quantity = quantity;
    cartInput.type = ConnectApi.CartItemType.PRODUCT;

    ConnectApi.CartItem cartItem = null;

    if(Test.isRunningTest() == false) {
      // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceCart_static_methods.htm#apex_ConnectAPI_CommerceCart_static_methods
      cartItem = ConnectApi.CommerceCart.addItemToCart(webstoreId, effectiveAccountId, 'active', cartInput);
    }

    return cartItem;
  }

  @AuraEnabled (cacheable=false)
  public static String getUserAccountID() {
      String userId = UserInfo.getUserId();
      String contactId = [SELECT ContactId FROM User WHERE Id = :userId].ContactId;
      // return Account Id for Buyer
      if (contactId != null ) {
          return [SELECT AccountId FROM Contact WHERE id=:contactId].AccountId;
      } else { // return default Account Id if user is an Admin
          return [SELECT AccountId FROM Contact WHERE Name Like '%Lauren Bailey%'].AccountId;
      }
  }

  // Function to lookup the webstore ID associated with the community
  public static String resolveCommunityIdToWebstoreId(String communityId) {
    if(communityId == null || communityId == '') {
        return null;
    }
    
    String webstoreId = null;

    if(Schema.sObjectType.WebStoreNetwork.fields.WebStoreId.isAccessible()
        && Schema.sObjectType.WebStoreNetwork.fields.NetworkId.isAccessible()) {
        List<WebStoreNetwork> wsnList = [SELECT WebStoreId FROM WebStoreNetwork WHERE NetworkId = :communityId];

        if(wsnList.size() > 0) {
            WebStoreNetwork wsn = wsnList.get(0);
            webstoreId = wsn.WebStoreId;
        }
    }

    return webstoreId;
  }

}