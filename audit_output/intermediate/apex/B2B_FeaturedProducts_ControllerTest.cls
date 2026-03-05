@IsTest
public with sharing class B2B_FeaturedProducts_ControllerTest {
    
    private static Id userId = null;
    private static Id accountId = null;
    private static Id storeId = null;
    private static Id productId = null;
    private static List<Product2> productList;

    private static final String sku = '655321';
    private static final String productName = 'Some Product';
    private static final String productDesc = 'Sample';

    private static String categoryId = null;
    private static String categoryId2 = null;

    private static void setupTestData() {

        System.debug('begin setupTestData()');

        accountId = B2B_FeaturedProducts_ControllerTestUtils.createAccount();

        userId = B2B_FeaturedProducts_ControllerTestUtils.createUser(null);

        System.debug('userId: ' + userId);

        Id pricebookId = B2B_FeaturedProducts_ControllerTestUtils.createPricebook();

        B2B_FeaturedProducts_ControllerTestUtils.assignPermissionSetToUser(userId, 'B2B_Featured_Products_Component');

        productId = B2B_FeaturedProducts_ControllerTestUtils.createProduct2(productName, sku, '');

            System.debug('productId: ' + productId);

        List<String> productIdList = new List<String>();
        productIdList.add(productId);

        productList = B2B_FeaturedProducts_ControllerTestUtils.getProducts(productIdList);

        B2B_FeaturedProducts_ControllerTestUtils.createStandardPricebookEntry(productId);

        B2B_FeaturedProducts_ControllerTestUtils.createPricebookEntry(pricebookId, productId);

    }

    private static void setupTestDataAdvanced() {

        String catalogId = B2B_FeaturedProducts_ControllerTestUtils.createProductCatalog();

        categoryId = B2B_FeaturedProducts_ControllerTestUtils.createProductCategory(catalogId, 'Everything');

        String pcpId = B2B_FeaturedProducts_ControllerTestUtils.createProductCategoryProduct(categoryId, productId);

        List<ProductCategoryProduct> pcpList = B2B_FeaturedProducts_ControllerTestUtils.getProductCategoryProducts(categoryId);

        categoryId2 = B2B_FeaturedProducts_ControllerTestUtils.createProductCategory(catalogId, 'Nothing');

        System.debug('pcpList.size (admin) = ' + pcpList.size());

    }

    /*
        getProductsByFieldValue - success
        Get a product using the StockKeepingUnit field value and equals
    */
    @IsTest(SeeAllData=true)
    public static void testCode1_1() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by SKU

            responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'StockKeepingUnit', sku, B2B_FeaturedProducts_Controller.FIELD_EQUALS, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(sku, retValue);

    }

    /*
        getProductsByFieldValue - Error condition
        Get a product using the ProductCode field value, a field the user won't have access to

        THIS IS NOT WORKING
    */
    // @IsTest(SeeAllData=false)
    // public static void testCode1_2_DNU() {

    //     User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

    //     System.runAs(adminUser) {
    //         setupTestData();
    //     }

    //     User storeUser = [Select Id, Name from User where Id = :userId];

    //     Boolean includePrices = true;

    //     Map<String, Object> responseMap = null;

    //     Test.startTest();

    //         System.runAs(storeUser) {

    //         // Get a product by SKU

    //         responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'ProductCode', sku, B2B_FeaturedProducts_Controller.FIELD_EQUALS, includePrices);

    //     }

    //     Test.stopTest();

    //     System.debug('responseMap: ' + JSON.serialize(responseMap));

    //     String jsonData = (String)responseMap.get('data');

    //     List<Object> productList = new List<Object>();

    //     if(jsonData != null) {
    //         productList = (List<Object>)JSON.deserializeUntyped(jsonData);
    //     }

    //     String retValue = null;

    //     for(Object obj : productList) {

    //         Map<String, Object> productMap = (Map<String, Object>)obj;

    //         Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

    //         Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

    //         retValue = (String)fieldValueMap.get('value');
    //     }

    //     System.debug('retValue: ' + retValue);

    //     System.assertEquals(null, retValue);

    // }

    /*
        getProductsByFieldValue - Error condition
        Get a product using an invalid field value, a field that doesn't exist
    */
    @IsTest(SeeAllData=true)
    public static void testCode1_3() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by invalid field name

            responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'BogusField__c', sku, B2B_FeaturedProducts_Controller.FIELD_EQUALS, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(null, retValue);

    }

    /*
        getProductsByFieldValue - Error condition
        Get a product using a field with an invalid type
    */
    @IsTest(SeeAllData=true)
    public static void testCode1_4() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by invalid field type

            responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'Description', productDesc, B2B_FeaturedProducts_Controller.FIELD_EQUALS, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(null, retValue);

    }

    /*
        getProductsByFieldValue - Error condition
        Get a product using a Boolean field with an invalid field value
    */
    @IsTest(SeeAllData=true)
    public static void testCode1_5() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by invalid Boolean value

            responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'IsActive', 'something', B2B_FeaturedProducts_Controller.FIELD_EQUALS, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(null, retValue);

    }

    /*
        getProductsByFieldValue - Error condition
        Get a product using an invalid field comparison value
    */
    @IsTest(SeeAllData=true)
    public static void testCode1_6() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by invalid comparison value

            responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'StockKeepingUnit', 'something', 'maybe', includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(null, retValue);

    }

    /*
        getProductsByFieldValue - success
        Get a product using the StockKeepingUnit field (String) value and contains
    */
    @IsTest(SeeAllData=true)
    public static void testCode1_7() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by SKU

            responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'StockKeepingUnit', '655', B2B_FeaturedProducts_Controller.FIELD_CONTAINS, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(sku, retValue);

    }

    /*
        getProductsByFieldValue - success
        Get a product using the IsActive field (Boolean) value and equals
    */
    @IsTest(SeeAllData=false)
    public static void testCode1_8() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by SKU

            responseMap = B2B_FeaturedProducts_Controller.getProductsByFieldValue(null, accountId, 'IsActive', 'true', B2B_FeaturedProducts_Controller.FIELD_EQUALS, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(sku, retValue);

    }

    /*
        getProductsBySku - success
        Get products using a valid list of SKUs
    */
    @IsTest(SeeAllData=false)
    public static void testCode2_1() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        List<String> skuList = new List<String>();
        skuList.add(sku);

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by SKU

            responseMap = B2B_FeaturedProducts_Controller.getProductsBySku(null, accountId, skuList, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(sku, retValue);

    }

    /*
        getProductsBySku - Error condition
        Get product using an empty SKU list
    */
    @IsTest(SeeAllData=false)
    public static void testCode2_2() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        List<String> skuList = new List<String>();

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get a product by SKU

            responseMap = B2B_FeaturedProducts_Controller.getProductsBySku(null, accountId, skuList, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(null, retValue);

    }

    /*
        getProductsByCategoryId - success
        Get products using a category Id

        NOTE: the SOQL query to get ProductCategoryProduct records fails as a store user, but works as an Admin user.
    */
    @IsTest(SeeAllData=false)
    public static void testCode3_1() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
            setupTestDataAdvanced();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        Map<String, Object> responseMap = null;

        Test.startTest();

        //System.runAs(storeUser) {

            List<ProductCategoryProduct> pcpList = B2B_FeaturedProducts_ControllerTestUtils.getProductCategoryProducts(categoryId);

            System.debug('pcpList.size (store user) = ' + pcpList.size());

            // Get products by category

            responseMap = B2B_FeaturedProducts_Controller.getProductsByCategoryId(null, accountId, categoryId, includePrices);

        //}

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        String successMsg = null;
        String errorMsg = null;

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String messagesJson = (String)responseMap.get('messagesJson');

        System.debug('messagesJson: ' + messagesJson);

        List<Object> messagesList = new List<Object>();

        if(messagesJson != null) {
            messagesList = (List<Object>)JSON.deserializeUntyped(messagesJson);
        }

        if(messagesList != null) {

            for(Object obj : messagesList) {
                Map<String, Object> messageMap = (Map<String, Object>)obj;

                String severity = (String)messageMap.get('severity');
                String message = (String)messageMap.get('message');

                if(severity == 'success') {
                    successMsg = message;
                }

                if(severity == 'error') {
                    errorMsg = message;
                }
            }

        }

        System.debug('successMsg: ' + successMsg);
        System.debug('errorMsg: ' + errorMsg);

        System.assertEquals(null, errorMsg);

        System.debug('retValue: ' + retValue);

        System.assertEquals(sku, retValue);

    }

    /*
        getProductsByCategoryId - error condition
        Get products using a null category Id
    */
    @IsTest(SeeAllData=false)
    public static void testCode3_2() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
            setupTestDataAdvanced();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        List<String> skuList = new List<String>();
        skuList.add(sku);

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get products by category

            responseMap = B2B_FeaturedProducts_Controller.getProductsByCategoryId(null, accountId, null, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(null, retValue);

    }

    /*
        getProductsByCategoryId - error condition
        Get products using a category with no products
    */
    @IsTest(SeeAllData=false)
    public static void testCode3_3() {

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
            setupTestDataAdvanced();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Boolean includePrices = true;

        List<String> skuList = new List<String>();
        skuList.add(sku);

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // Get products by category

            responseMap = B2B_FeaturedProducts_Controller.getProductsByCategoryId(null, accountId, categoryId2, includePrices);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String jsonData = (String)responseMap.get('data');

        List<Object> productList = new List<Object>();

        if(jsonData != null) {
            productList = (List<Object>)JSON.deserializeUntyped(jsonData);
        }

        String retValue = null;

        for(Object obj : productList) {

            Map<String, Object> productMap = (Map<String, Object>)obj;

            Map<String, Object> fieldsMap = (Map<String, Object>)productMap.get('fields');

            Map<String, Object> fieldValueMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retValue = (String)fieldValueMap.get('value');
        }

        System.debug('retValue: ' + retValue);

        System.assertEquals(null, retValue);

    }

    @IsTest
    /*
        one valid SKU, one invalid SKU
        hasHeaderRow = true
        ignoreInvalidSkus = false
        emailResults = false
    */
    public static void testGetInfo() {

        System.debug('begin testGetInfo()');

        User adminUser = B2B_FeaturedProducts_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        Test.startTest();

        System.runAs(storeUser) {

            // Don't do any DML prior to making this call:

            responseMap = B2B_FeaturedProducts_Controller.fetchInitValues(null, accountId);

        }

        Test.stopTest();

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String effectiveAccountId = (String)responseMap.get('effectiveAccountId');

        System.assertEquals(accountId, effectiveAccountId);

    }

}