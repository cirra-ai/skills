/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */

@IsTest
public with sharing class B2BCrossSellTest {

    private static Id userId = null;
    private static Id accountId = null;
    
    private static Id parentProductId;
    private static Id crossProductId;
    private static Id crossItemId;
    private static Id crossPbeId;
    private static Id crossStdPbeId;

    private static String crossProductSku = '999AAA000222';

    private static void setupTestData() {

        accountId = B2BCrossSellTestUtils.createAccount();

        userId = B2BCrossSellTestUtils.createUser(null);

        System.debug('userId: ' + userId);

        B2BCrossSellTestUtils.assignPermissionSetToUser(userId, 'B2B_Cross_Sell_Recommendations_User');

        parentProductId =  B2BCrossSellTestUtils.createProduct('Parent Product', '999AAA000111', '');

        crossProductId =  B2BCrossSellTestUtils.createProduct('Cross Product', crossProductSku, '');

        crossItemId = B2BCrossSellTestUtils.createCrossSellItem(parentProductId, crossProductId, null);

        B2BCrossSellTestUtils.createCrossSellItem(parentProductId, crossProductId, 'CrossSell');

        Id pricebookId = B2BCrossSellTestUtils.createPricebook();

        B2BCrossSellTestUtils.createStandardPricebookEntry(parentProductId);

        B2BCrossSellTestUtils.createPricebookEntry(pricebookId, parentProductId);

        crossStdPbeId = B2BCrossSellTestUtils.createStandardPricebookEntry(crossProductId);

        crossPbeId = B2BCrossSellTestUtils.createPricebookEntry(pricebookId, crossProductId);

    }
    
    @IsTest
    /*
        Test getting the product detail with no product type specified
    */
    public static void testCode1() {

        User adminUser = B2BCrossSellTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String communityId = null;
        String effectiveAccountID = null;

        List<ConnectApi.ProductDetail> myProductsInformations = null;

        Test.startTest();

        System.runAs(storeUser) {

            myProductsInformations = B2BCrossSell.getCrossSellProducts(communityId, parentProductId, effectiveAccountID, null);

        }

        Test.stopTest();

        System.debug('myProductsInformations: ' + JSON.serialize(myProductsInformations));

        ConnectApi.ProductDetail pd = null;

        pd = myProductsInformations.get(0);

        Map<String, String> fieldMap = pd.fields;

        Product2 product = B2BCrossSellTestUtils.getProduct(crossProductId);

        String sku = fieldMap.get('StockKeepingUnit');

        System.assertEquals(crossProductSku, sku);
    }

    @IsTest
    /*
        Test getting the product price
    */
    public static void testCode2() {

        User adminUser = B2BCrossSellTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String communityId = null;
        String effectiveAccountID = null;

        ConnectApi.ProductPrice price = null;

        Test.startTest();

        System.runAs(storeUser) {

            price = B2BCrossSell.getProductPrice(communityId, crossProductId, effectiveAccountID);

        }

        Test.stopTest();

        System.debug('price: ' + JSON.serialize(price));

        String listPrice = price.listPrice;
        String unitPrice = price.unitPrice;

        PricebookEntry pbe = B2BCrossSellTestUtils.getPricebookEntry(crossStdPbeId, crossProductId);

        System.assertEquals(listPrice, pbe.UnitPrice.format());

        PricebookEntry pbe2 = B2BCrossSellTestUtils.getPricebookEntry(crossPbeId, crossProductId);

        System.assertEquals(unitPrice, pbe2.UnitPrice.format());

    }

    @IsTest
    /*
        Test adding to the cart
    */
    public static void testCode3() {

        User adminUser = B2BCrossSellTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String communityId = null;
        String effectiveAccountID = null;

        ConnectApi.CartItem cartItem = null;

        Test.startTest();

        System.runAs(storeUser) {

            cartItem = B2BCrossSell.addToCart(communityId, crossProductId, '1', effectiveAccountID);

        }

        Test.stopTest();

        System.assertEquals(cartItem, null);

    }

    @IsTest
    /*
        Test the search page url function
    */
    public static void testCode4() {

        User adminUser = B2BCrossSellTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String myCurrentProductURL = null;

        Test.startTest();

        System.runAs(storeUser) {

            myCurrentProductURL = B2BCrossSell.searchCurrentProductPageURL();

        }

        Test.stopTest();

        System.debug(myCurrentProductURL);
        
        Boolean checkIt = myCurrentProductURL.endsWith('/s/product/');

        System.assertEquals(checkIt, true);

    }

    @IsTest
    /*
        Test getting the product detail with a product type specified
    */
    public static void testCode5() {

        User adminUser = B2BCrossSellTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String communityId = null;
        String effectiveAccountID = null;

        List<ConnectApi.ProductDetail> myProductsInformations = null;

        Test.startTest();

        System.runAs(storeUser) {

            myProductsInformations = B2BCrossSell.getCrossSellProducts(communityId, parentProductId, effectiveAccountID, 'CrossSell');

        }

        Test.stopTest();

        System.debug('myProductsInformations: ' + JSON.serialize(myProductsInformations));

        ConnectApi.ProductDetail pd = null;

        pd = myProductsInformations.get(0);

        Map<String, String> fieldMap = pd.fields;

        Product2 product = B2BCrossSellTestUtils.getProduct(crossProductId);

        String sku = fieldMap.get('StockKeepingUnit');

        System.assertEquals(crossProductSku, sku);
    }

}