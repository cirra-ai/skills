@IsTest
public with sharing class SDO_B2B_Cart_CustomValidationTest {

    private static Id userId = null;
    private static Id accountId = null;
    private static Id storeId = null;
    private static Id productId = null;
    private static List<Product2> productList;

    private static final String sku = '655321';
    private static final String productName = 'Some Product';
    private static final String productDesc = 'Sample';

    public static String webstoreId = null;
    public static Id cartId = null;

    private static void setupTestData() {

        System.debug('begin setupTestData()');

        accountId = SDO_B2B_Cart_CustomValidationTestUtils.createAccount();

        userId = SDO_B2B_Cart_CustomValidationTestUtils.createUser(null);

        System.debug('userId: ' + userId);

        Id pricebookId = SDO_B2B_Cart_CustomValidationTestUtils.createPricebook();

        SDO_B2B_Cart_CustomValidationTestUtils.assignPermissionSetToUser(userId, 'B2B_LE_Cart_Validation_Users');

        productId = SDO_B2B_Cart_CustomValidationTestUtils.createProduct2(productName, sku, '');

            System.debug('productId: ' + productId);

        List<String> productIdList = new List<String>();
        productIdList.add(productId);

        productList = SDO_B2B_Cart_CustomValidationTestUtils.getProducts(productIdList);

        SDO_B2B_Cart_CustomValidationTestUtils.createStandardPricebookEntry(productId);

        SDO_B2B_Cart_CustomValidationTestUtils.createPricebookEntry(pricebookId, productId);

        WebStore webStore = new WebStore(Name='TestWebStore', SupportedLanguages='en_US', DefaultLanguage='en_US');
        insert webStore;
        webstoreId = webStore.Id;

    }

    private static void setupTestData2() {

        WebCart cart = new WebCart(
            Name='Cart'
            , WebStoreId = webStoreId
            , AccountId = accountId
            , PONumber = '24601'
            , Status = 'Active'
            , Type = 'Cart'
            , BillingStreet = '2100 Woodward Ave'
            
            , BillingCity = 'Detroit'
            , BillingState = 'MI'
            , BillingPostalCode = '48201'
            , BillingCountry = 'USA'
            , Custom_Message_Type__c = 'Error'
            , Custom_Message_Text__c = 'Error!'
            );
        insert cart;
        cartId = cart.Id;

        System.debug('cartId: ' + cartId);

    }

    @IsTest
    /*
        Test getting the product detail with no product type specified
    */
    public static void testCode1() {

        User adminUser = SDO_B2B_Cart_CustomValidationTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String communityId = null;
        String effectiveAccountID = null;

        Map<String, Object> responseMap = null;

        Test.startTest();

        System.runAs(storeUser) {

            // Create the cart as the store user
            setupTestData2();

            responseMap = SDO_B2B_Cart_CustomValidation.fetchCustomCartValidation(cartId);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String customMessageType = (String)responseMap.get('customMessageType');

        String customMessageText = (String)responseMap.get('customMessageText');

        List<WebCart> cartList = [Select Id, Custom_Message_Type__c, Custom_Message_Text__c from WebCart where Id = :cartId];

        WebCart cart = cartList.get(0);

        System.assertEquals(cart.Custom_Message_Type__c, customMessageType);

        System.assertEquals(cart.Custom_Message_Text__c, customMessageText);
    }
    
    @IsTest
    /*
        Test getting info with a cartId
    */
    public static void testGetInfo1() {

        System.debug('begin testGetInfo1()');

        User adminUser = SDO_B2B_Cart_CustomValidationTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        Test.startTest();

        System.runAs(storeUser) {

            // Create the cart as the store user
            setupTestData2();

            // Don't do any DML prior to making this call:

            responseMap = SDO_B2B_Cart_CustomValidation.fetchInitValues(null, accountId, cartId);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String effectiveAccountId = (String)responseMap.get('effectiveAccountId');

        System.assertEquals(accountId, effectiveAccountId);

    }

    @IsTest
    /*
        Test getting info with a null cartId
    */
    public static void testGetInfo2() {

        System.debug('begin testGetInfo2()');

        User adminUser = SDO_B2B_Cart_CustomValidationTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        Test.startTest();

        System.runAs(storeUser) {

            // Don't do any DML prior to making this call:

            responseMap = SDO_B2B_Cart_CustomValidation.fetchInitValues(null, accountId, null);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String returnedCartId = (String)responseMap.get('cartId');

        System.assertEquals(null, returnedCartId);

    }

    /*
        Work the util methods
    */
    @isTest static void testCode2() {
        Map<String, Object> responseMap = new Map<String, Object>();
        SDO_B2B_Cart_CustomValidation.addMessage(new SDO_B2B_Cart_CustomValidation.Message('Error', 'Some error message', SDO_B2B_Cart_CustomValidation.ERROR), 0, responseMap);
        SDO_B2B_Cart_CustomValidation.addMessage(new SDO_B2B_Cart_CustomValidation.Message('Error', 'Some error message', SDO_B2B_Cart_CustomValidation.ERROR), null, responseMap);
        SDO_B2B_Cart_CustomValidation.addMessage(new SDO_B2B_Cart_CustomValidation.Message('Error', 'Some error message', SDO_B2B_Cart_CustomValidation.ERROR), 0, responseMap);
        SDO_B2B_Cart_CustomValidation.addMessage(new SDO_B2B_Cart_CustomValidation.Message('Error', 'Some error message', SDO_B2B_Cart_CustomValidation.ERROR, true), 0, responseMap);
    }

}