/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */

// https://trailhead.salesforce.com/en/content/learn/modules/apex_testing

public with sharing class B2BBundle {
  @AuraEnabled(cacheable=true)
  public static List<ConnectApi.ProductDetail> getBundleProducts(
    String communityId,
    String productID,
    String effectiveAccountID
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreID = resolveCommunityIdToWebstoreId(communityId);
    //System.Debug('****** webstoreID -' + webstoreID);
    //System.Debug('****** productID -' + productID);
    //System.Debug('****** effectiveAccountID -' + effectiveAccountID);

    //New list to received products details
    List<ConnectApi.ProductDetail> myProductsInformations = new List<ConnectApi.ProductDetail>();

    // Need Sharing Setting for external user on this object
    List<Bundle_Item__c> myProductsID = new List<Bundle_Item__c>();
    
    if(Schema.sObjectType.Bundle_Item__c.fields.Bundle_Item__c.isAccessible()
        && Schema.sObjectType.Bundle_Item__c.fields.Bundle_Parent_Item__c.isAccessible()) {

        myProductsID = [
          SELECT Bundle_Item__c
          FROM Bundle_Item__c
          WHERE Bundle_Parent_Item__c = :productID
        ];

    }

    Integer count = 0;
    ConnectApi.ProductDetail myproduct;
    for (Bundle_Item__c myRelatedProductId : myProductsID) {
      myproduct = B2BBundle.getProduct(
        webstoreID,
        myRelatedProductId.Bundle_Item__c,
        effectiveAccountID
      );

      myProductsInformations.add(myproduct);

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
      // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceCatalog_static_methods.htm#apex_ConnectAPI_CommerceCatalog_static_methods
      pd = ConnectApi.CommerceCatalog.getProduct(webstoreId, productId, effectiveAccountID, null, false, null, false, true, false);
    }
    else {
      pd = B2BBundleTestUtils.getProductDetail(productId);
    }

    return pd;
  }

  @AuraEnabled(cacheable=true)
  public static String searchCurrentProductPageURL() {
    //Retrieve Community ID
    String myNetworkID = Network.getNetworkId();

    String UrlPathPrefix = '';

    List<Network> list1 = [
      SELECT UrlPathPrefix
      FROM Network
      WHERE Id = :myNetworkID
    ];

    if (list1.size() > 0) {
      if(list1.get(0).UrlPathPrefix != null) {
        UrlPathPrefix = list1.get(0).UrlPathPrefix + '/';
      }
      }

    String myDomain = '';
    List<Domain> list2 = [SELECT Domain FROM Domain];

    if (list2.size() > 0) {
      myDomain = list2.get(0).Domain;
    }

    String myCurrentProductURL =
      'https://' +
      myDomain +
      '/' +
      UrlPathPrefix +
      's/product/';
    //system.debug(myCurrentProductURL);
    return myCurrentProductURL;
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

    ConnectApi.ProductPrice price = null;

    if(Test.isRunningTest() == false) {
      // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceStorePricing_static_methods.htm#apex_ConnectAPI_CommerceStorePricing_static_methods
      price = ConnectApi.CommerceStorePricing.getProductPrice(webstoreId, productId, effectiveAccountId );
    }
    else {
      price = B2BBundleTestUtils.getProductPrice(productId);
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

  // Function to lookup the webstore ID associated with the community
  @AuraEnabled
  public static Decimal getItemQuantity(
    String currentProductId,
    String myBundleItem
  ) {

    Decimal qty = null;

    if(Schema.sObjectType.Bundle_Item__c.fields.Bundle_Item__c.isAccessible()
        && Schema.sObjectType.Bundle_Item__c.fields.Bundle_Parent_Item__c.isAccessible()
        && Schema.sObjectType.Bundle_Item__c.fields.Quantity__c.isAccessible()
        ) {
        qty = [
          SELECT Quantity__c
          FROM Bundle_Item__c
          WHERE
            Bundle_Item__c = :myBundleItem
            AND Bundle_Parent_Item__c = :currentProductId
          LIMIT 1
        ]
        .Quantity__c;
    }

    return qty;
  }

}