@IsTest
public with sharing class B2B_Moodboard_ControllerTest {

    private static Id userId = null;
    private static Id accountId = null;
    private static Id storeId;
    private static Id productId = null;
    private static List<Product2> productList;

    private static final String sku = '655321';
    private static final String productName = 'Some Product';

    private static void setupTestData() {

        System.debug('begin setupTestData()');

        accountId = B2B_Moodboard_ControllerTestUtils.createAccount();

        userId = B2B_Moodboard_ControllerTestUtils.createUser(null);

        System.debug('userId: ' + userId);

        Id pricebookId = B2B_Moodboard_ControllerTestUtils.createPricebook();

        B2B_Moodboard_ControllerTestUtils.assignPermissionSetToUser(userId, 'B2B_LE_Moodboard_User');

        productId = B2B_Moodboard_ControllerTestUtils.createProduct2(productName, sku, '');

            System.debug('productId: ' + productId);

        List<String> productIdList = new List<String>();
        productIdList.add(productId);

        productList = B2B_Moodboard_ControllerTestUtils.getProducts(productIdList);

        B2B_Moodboard_ControllerTestUtils.createStandardPricebookEntry(productId);

        B2B_Moodboard_ControllerTestUtils.createPricebookEntry(pricebookId, productId);

    }

    /*
        Save a new moodboard
    */
    @IsTest(SeeAllData=true)
    public static void testCode1() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // SAVE A NEW MOODBOARD

            String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

            responseMap = B2B_Moodboard_Controller.saveMoodBoard(userId, null, 'Test MB 1', accountId, jsonData);            

        }

        Test.stopTest();

        String successMsg = null;
        String errorMsg = null;

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String messagesJson = (String)responseMap.get('messagesJson');

        System.debug('messagesJson: ' + messagesJson);

        List<Object> messagesList = (List<Object>)JSON.deserializeUntyped(messagesJson);

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

        System.debug('successMsg: ' + successMsg);
        System.debug('errorMsg: ' + errorMsg);

        System.assertNotEquals(null, successMsg);

    }

    /*
        Get existing moodboard names (used by the component in a combo box)
    */
    @IsTest(SeeAllData=true)
    public static void testCode2() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String moodboardName = 'Test MB 1';

        Map<String, String> moodBoardMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // SAVE A NEW MOODBOARD

            String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

            B2B_Moodboard_Controller.saveMoodBoard(userId, null, moodboardName, accountId, jsonData);

            // GET THE EXISTING MOODBOARD NAMES AND IDS

            moodBoardMap = B2B_Moodboard_Controller.getMoodBoardNames(userId, accountId);

        }

        Test.stopTest();

        // GET THE ID AND NAME OF THE FIRST MOODBOARD RETURNED

        String savedMoodboardName = null;

        for(String moodboardId : moodBoardMap.keySet()) {
            savedMoodboardName = moodBoardMap.get(moodboardId);
            break;
        }

        System.assertEquals(moodboardName, savedMoodboardName);

    }

    /*
        Resave an existing moodboard with a modified name
    */
    @IsTest(SeeAllData=true)
    public static void testCode3() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String moodboardName1 = 'Test MB 1';
        String moodboardName2 = 'Test MB 1.1';

        Map<String, String> moodBoardMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // SAVE A NEW MOODBOARD

            String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

            B2B_Moodboard_Controller.saveMoodBoard(userId, null, moodboardName1, accountId, jsonData);

            // GET THE MOODBOARD ID

            moodBoardMap = B2B_Moodboard_Controller.getMoodBoardNames(userId, accountId);

            Set<String> moodboardIds = moodBoardMap.keySet();

            String moodboardId = null;

            for(String mbId : moodBoardMap.keySet()) {
                moodboardId = mbId;
                break;
            }

            // RE-SAVE THE MOODBOARD
            Map<String, Object> responseMap2 = B2B_Moodboard_Controller.saveMoodBoard(userId, moodboardId, moodboardName2, accountId, jsonData);

            // GET THE MOODBOARD ID (again)

            moodBoardMap = B2B_Moodboard_Controller.getMoodBoardNames(userId, accountId);

        }

        Test.stopTest();

        // GET THE ID AND NAME OF THE FIRST MOODBOARD RETURNED

        String savedMoodboardName = null;

        for(String moodboardId : moodBoardMap.keySet()) {
            savedMoodboardName = moodBoardMap.get(moodboardId);
            break;
        }

        System.assertEquals(moodboardName2, savedMoodboardName);

    }

    /*
        Get the data for an existing moodboard (product detail only)
    */
    @IsTest(SeeAllData=true)
    public static void testCode4() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        String data = null;

        String moodboardName = 'Test MB 1';

        Test.startTest();

            System.runAs(storeUser) {

            // SAVE A NEW MOODBOARD

            String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

            responseMap = B2B_Moodboard_Controller.saveMoodBoard(userId, null, moodboardName, accountId, jsonData);

            // GET THE EXISTING MOODBOARD NAMES AND IDS

            Map<String, String> moodBoardMap = B2B_Moodboard_Controller.getMoodBoardNames(userId, accountId);

            // GET THE ID OF THE FIRST MOODBOARD RETURNED

            Set<String> moodboardIds = moodBoardMap.keySet();

            String moodboardId = null;

            for(String mbId : moodBoardMap.keySet()) {
                moodboardId = mbId;
                break;
            }

            // GET THE MOODBOARD DATA, NO PRICING (requires ConnectApi call)
            
            data = B2B_Moodboard_Controller.getMoodBoardData(userId, moodBoardId, null, storeId, accountId, false);
            

        }

        Test.stopTest();

        System.debug('data: ' + data);

        List<Object> dataList = (List<Object>)JSON.deserializeUntyped(data);

        for(Object dataObj : dataList) {

            Map<String, Object> dataMap = (Map<String, Object>)dataObj;

            Map<String, Object> fieldsMap = (Map<String, Object>)dataMap.get('fields');

            Map<String, Object> fieldMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            String value = (String)fieldMap.get('value');

            System.debug('value: ' + value);

        }

    }

    /*
        Get the data for an existing moodboard (product detail and pricing)
    */
    @IsTest(SeeAllData=true)
    public static void testCode5() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        String data = null;

        String moodboardName = 'Test MB 1';

        Test.startTest();

            System.runAs(storeUser) {

            // SAVE A NEW MOODBOARD

            String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

            responseMap = B2B_Moodboard_Controller.saveMoodBoard(userId, null, moodboardName, accountId, jsonData);

            // GET THE EXISTING MOODBOARD NAMES AND IDS

            Map<String, String> moodBoardMap = B2B_Moodboard_Controller.getMoodBoardNames(userId, accountId);

            // GET THE ID OF THE FIRST MOODBOARD RETURNED

            Set<String> moodboardIds = moodBoardMap.keySet();

            String moodboardId = null;

            for(String mbId : moodBoardMap.keySet()) {
                moodboardId = mbId;
                break;
            }

            // GET THE MOODBOARD DATA, NO PRICING (requires ConnectApi call)
            
            data = B2B_Moodboard_Controller.getMoodBoardData(userId, moodBoardId, null, storeId, accountId, true);
            
        }

        Test.stopTest();

        System.debug('data: ' + data);

        List<Object> dataList = (List<Object>)JSON.deserializeUntyped(data);

        String retrievedSku = null;
        String retrievedPrice = null;

        for(Object dataObj : dataList) {

            Map<String, Object> dataMap = (Map<String, Object>)dataObj;

            Map<String, Object> fieldsMap = (Map<String, Object>)dataMap.get('fields');

            Map<String, Object> fieldMap = (Map<String, Object>)fieldsMap.get('StockKeepingUnit');

            retrievedSku = (String)fieldMap.get('value');

            System.debug('retrievedSku: ' + retrievedSku);

            Map<String, Object> prices = (Map<String, Object>)dataMap.get('prices');

            retrievedPrice = (String)prices.get('listPrice');

        }

        System.assertEquals(sku, retrievedSku);
        System.assertEquals(retrievedPrice, '1.98');

    }

    /*
        Test the product search
    */
    @IsTest(SeeAllData=true)
    public static void testCode6() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        Test.setMock(HttpCalloutMock.class, new B2B_Moodboard_ProductSearchRestApiMock(productList));

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        Map<String, Object> response = null;

        String communityId = null;

        Test.startTest();

            System.runAs(storeUser) {

                response = B2B_Moodboard_Controller.getProducts(sku, communityId, storeId, accountId, true, 25, null);
            
            }

        Test.stopTest();

        System.debug('response: ' + response);

        

    }

    /*
        Save a new moodboard with no name specified.  Will throw an Exception in the underlying code.
    */
    @IsTest(SeeAllData=true)
    public static void testCode7() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        Map<String, Object> responseMap = null;

        String moodboardName = null;

        Test.startTest();

            System.runAs(storeUser) {

            // SAVE A NEW MOODBOARD

            String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

            responseMap = B2B_Moodboard_Controller.saveMoodBoard(userId, null, moodboardName, accountId, jsonData);            

        }

        Test.stopTest();

        String successMsg = null;
        String errorMsg = null;

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String messagesJson = (String)responseMap.get('messagesJson');

        System.debug('messagesJson: ' + messagesJson);

        List<Object> messagesList = (List<Object>)JSON.deserializeUntyped(messagesJson);

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

        System.debug('successMsg: ' + successMsg);
        System.debug('errorMsg: ' + errorMsg);

        System.assertNotEquals(null, errorMsg);

    }

    /*
        Test adding a moodboard to the cart.
        The ConnectApi.CommerceCart.addItemsToTheCart() call is short-circuited in the actual code.
    */
    @IsTest(SeeAllData=true)
    public static void testCode8() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String communityId = null;

        Map<String, Object> responseMap = null;

        String moodboardName = 'Test MB 1';

        Test.startTest();

            System.runAs(storeUser) {

                String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

                // Add the moodboard data to the cart

                responseMap = B2B_Moodboard_Controller.addMoodBoardProductsToTheCart(userId, communityId, storeId, moodBoardName, accountId, 'active', jsonData);

            }

        Test.stopTest();

        String successMsg = null;
        String errorMsg = null;

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String messagesJson = (String)responseMap.get('messagesJson');

        System.debug('messagesJson: ' + messagesJson);

        List<Object> messagesList = (List<Object>)JSON.deserializeUntyped(messagesJson);

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

        Integer totItems = (Integer)responseMap.get('totItems');

        System.assertEquals(1, totItems);

    }

    /*
        Test adding a moodboard to the cart with more products than is allowed.
        The ConnectApi.CommerceCart.addItemsToTheCart() call is short-circuited in the actual code.
    */
    @IsTest(SeeAllData=true)
    public static void testCode9() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String communityId = null;

        Map<String, Object> responseMap = null;

        String moodboardName = 'Test MB 1';

        Integer totProducts = 101;

        Test.startTest();

            System.runAs(storeUser) {

                String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardDataExceedsMax(totProducts);

                // Add the moodboard data to the cart

                responseMap = B2B_Moodboard_Controller.addMoodBoardProductsToTheCart(userId, communityId, storeId, moodBoardName, accountId, 'active', jsonData);

            }

        Test.stopTest();

        String successMsg = null;
        String errorMsg = null;

        System.debug('responseMap: ' + JSON.serialize(responseMap));

        String messagesJson = (String)responseMap.get('messagesJson');

        System.debug('messagesJson: ' + messagesJson);

        List<Object> messagesList = (List<Object>)JSON.deserializeUntyped(messagesJson);

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

        Integer totErrors = (Integer)responseMap.get('totErrors');

        System.assertEquals(totProducts, totErrors);

    }

    /*
        Resave an existing moodboard with a modified name
    */
    @IsTest(SeeAllData=true)
    public static void testCode10() {

        User adminUser = B2B_Moodboard_ControllerTestUtils.createAdminUser();

        System.runAs(adminUser) {
            setupTestData();
        }

        User storeUser = [Select Id, Name from User where Id = :userId];

        String moodboardName1 = 'Test MB 1';

        Map<String, String> moodBoardMap = null;

        Test.startTest();

            System.runAs(storeUser) {

            // SAVE A NEW MOODBOARD

            String jsonData = B2B_Moodboard_ControllerTestUtils.createMoodBoardData(productId, 1);

            B2B_Moodboard_Controller.saveMoodBoard(userId, null, moodboardName1, accountId, jsonData);

            // GET THE MOODBOARD ID

            moodBoardMap = B2B_Moodboard_Controller.getMoodBoardNames(userId, accountId);

            Set<String> moodboardIds = moodBoardMap.keySet();

            String moodboardId = null;

            for(String mbId : moodBoardMap.keySet()) {
                moodboardId = mbId;
                break;
            }

            // DELETE THE MOODBOARD
            Map<String, Object> responseMap2 = B2B_Moodboard_Controller.deleteMoodBoard(moodboardId);

            // GET THE MOODBOARD ID (again)

            moodBoardMap = B2B_Moodboard_Controller.getMoodBoardNames(userId, accountId);

        }

        Test.stopTest();

        // GET THE ID AND NAME OF THE FIRST MOODBOARD RETURNED

        String savedMoodboardName = null;

        for(String moodboardId : moodBoardMap.keySet()) {
            savedMoodboardName = moodBoardMap.get(moodboardId);
            break;
        }

        System.assertEquals(null, savedMoodboardName);

    }
    
}