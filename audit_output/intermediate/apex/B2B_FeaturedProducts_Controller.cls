public with sharing class B2B_FeaturedProducts_Controller {

    private static final Integer MAX_PRODUCTS = 24;

    public static final String FIELD_CONTAINS = 'contains';
    public static final String FIELD_EQUALS = 'equals';

    @AuraEnabled (cacheable=false)
    public static Map<String, Object> getProductsByFieldValue(String webstoreId, String effectiveAccountId, String fieldApiName, String fieldValue, String compareType, Boolean includePrices) {

        System.debug('inside getProductsByFieldValue()');

        // System.debug('webstoreId: ' + webstoreId);
        // System.debug('effectiveAccountId: ' + effectiveAccountId);
        // System.debug('fieldApiName: ' + fieldApiName);
        // System.debug('fieldValue: ' + fieldValue);
        // System.debug('includePrices: ' + includePrices);

        Map<String, Object> responseMap = new Map<String, Object>();
        
        String data = null;

        List<Object> featuredProductList = new List<Object>();

        try {

            // Check to see if the field name is valid
            Set<String> objectFieldNames = Schema.SObjectType.Product2.fields.getMap().keySet();

            if(objectFieldNames.contains(fieldApiName.toLowerCase()) == false) {

                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(
                        Label.B2B_FP_Component_configuration_error, 
                        Label.B2B_FP_Invalid_Field_for_Product_Object.replace('{0}', fieldApiName), 
                        B2B_FeaturedProducts_Util.ERROR), 
                        0, responseMap);

                throw new CustomException('Component configuration error');

            }

            if(B2B_FeaturedProducts_SecurityUtils.checkIsAccessible('Product2', new String[]{fieldApiName}) == false) {
                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(
                    Label.B2B_FP_Component_configuration_error, Label.B2B_FP_Field_is_not_accessible.replace('{0}', fieldApiName), B2B_FeaturedProducts_Util.ERROR), 0, responseMap);

                throw new CustomException('Component configuration error');
            }

            // Check to see if the field type is allowed (String, Picklist or Boolean)

            Map<String, Schema.SObjectField> objectFieldMap = Schema.SObjectType.Product2.fields.getMap();

            Schema.SObjectField field = objectFieldMap.get(fieldApiName);

            Schema.DisplayType fieldType = field.getDescribe().getType();

            if(fieldType != Schema.DisplayType.String && fieldType != Schema.DisplayType.Picklist && fieldType != Schema.DisplayType.Boolean) {
                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(
                    Label.B2B_FP_Component_configuration_error, 
                        Label.B2B_FP_Invalid_Field_Type.replace('{0}', fieldApiName), 
                        B2B_FeaturedProducts_Util.ERROR), 
                        0, responseMap);

                throw new CustomException('Component configuration error');
            }

            // System.debug('fieldType: ' + fieldType);

            // If the field is a Boolean, make sure the comparison value is true or false

            if(fieldType == Schema.DisplayType.Boolean && (fieldValue.toLowerCase() != 'true' && fieldValue.toLowerCase() != 'false')) {

                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(
                    Label.B2B_FP_Component_configuration_error, 
                    Label.B2B_FP_Invalid_Boolean_Field_Value.replace('{0}', fieldApiName), 
                        B2B_FeaturedProducts_Util.ERROR), 
                        0, responseMap);

                throw new CustomException('Component configuration error');

            }

            if(compareType != FIELD_CONTAINS && compareType != FIELD_EQUALS) {

                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(
                    Label.B2B_FP_Component_configuration_error, 
                        Label.B2B_FP_Invalid_Compare_Type, 
                        B2B_FeaturedProducts_Util.ERROR), 
                        0, responseMap);

                throw new CustomException('Component configuration error');

            }

            List<B2B_FeaturedProducts_Util.ProductDetailWrapper> productList = new List<B2B_FeaturedProducts_Util.ProductDetailWrapper>();

            List<Product2> standardProductList = new List<Product2>();

            // Query using a dynamic SOQL statement

            String searchText = null;
            String query = null;

            if(fieldType == Schema.DisplayType.Picklist || fieldType == Schema.DisplayType.String) {
                if(compareType == 'contains') {
                    searchText = '\'%' + String.escapeSingleQuotes(fieldValue.trim()) + '%\'';

                    query = 'SELECT Id' +
                    ' FROM Product2' +
                    ' WHERE ' + string.escapeSingleQuotes(fieldApiName) + ' LIKE ' + searchText +
                    ' AND IsActive = TRUE' +
                    ' LIMIT ' + MAX_PRODUCTS;

                }
                else {
                    searchText = '\'' + String.escapeSingleQuotes(fieldValue.trim()) + '\'';

                    query = 'SELECT Id' +
                    ' FROM Product2' +
                    ' WHERE ' + string.escapeSingleQuotes(fieldApiName) + ' = ' + searchText +
                    ' AND IsActive = TRUE' +
                    ' LIMIT ' + MAX_PRODUCTS;
                }
            }
            else if(fieldType == Schema.DisplayType.Boolean) {

                searchText = String.escapeSingleQuotes(fieldValue.trim());

                query = 'SELECT Id' +
                    ' FROM Product2' +
                    ' WHERE ' + string.escapeSingleQuotes(fieldApiName) + ' = ' + searchText + 
                    ' AND IsActive = TRUE' +
                    ' LIMIT ' + MAX_PRODUCTS;
            }

            //System.debug('query: ' + query);

            List<sObject> sobjList = Database.query(query);

            for (SObject s : sobjList) {
                standardProductList.add((Product2)s);
            }

            //System.debug('standardProductList.size = ' + standardProductList.size());

            // The following List is used only for test coverage purposes.
            List<String> productIdList = new List<String>();

            for(Product2 standardProduct : standardProductList) {

                String productId = standardProduct.Id;

                productIdList.add(productId);

            }

            featuredProductList = getProductDetails(productIdList, webstoreId, effectiveAccountId);

            //System.debug('featuredProductList: ' + JSON.serialize(featuredProductList));

            if(includePrices && featuredProductList.size() > 0) {
                getProductPriceDetails(featuredProductList, webstoreId, effectiveAccountId);
            }

            // System.debug('featuredProductList: ' + JSON.serialize(featuredProductList));

            data = JSON.serialize(featuredProductList);

            responseMap.put('data', data);

        }
        catch (CustomException ce) {}
        catch (Exception err) {

            System.debug(Label.B2B_FP_Processing_Error + ': ' + err.getMessage());
            System.debug('Line #: ' + err.getLineNumber());
            System.debug(err.getStackTraceString());

            B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(Label.B2B_FP_Processing_Error, err.getMessage(), B2B_FeaturedProducts_Util.ERROR), 0, responseMap);

        }

        responseMap.put('totItems', featuredProductList.size());

        List<B2B_FeaturedProducts_Util.Message> retMessages = (List<B2B_FeaturedProducts_Util.Message>)responseMap.get('messages');

        if(retMessages == null) {
            retMessages = new List<B2B_FeaturedProducts_Util.Message>();
        }

        String messagesJson = JSON.serialize(retMessages);
        // System.debug('messagesJson: ' + messagesJson);
        responseMap.put('messagesJson', messagesJson);

        return responseMap;

    }

    @AuraEnabled (cacheable=false)
    public static Map<String, Object> getProductsBySku(String webstoreId, String effectiveAccountId, List<String> skuList, Boolean includePrices) {

        System.debug('inside getProductsBySku()');

        // System.debug('webstoreId: ' + webstoreId);
        // System.debug('effectiveAccountId: ' + effectiveAccountId);
        // System.debug('skuList: ' + skuList);
        // System.debug('includePrices: ' + includePrices);

        Map<String, Object> responseMap = new Map<String, Object>();
        
        String data = null;

        List<Object> featuredProductList = new List<Object>();

        List<B2B_FeaturedProducts_Util.ProductDetailWrapper> productList = new List<B2B_FeaturedProducts_Util.ProductDetailWrapper>();

        if(skuList.size() <= 0) {

            B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(
                    Label.B2B_FP_Component_configuration_error, 
                    Label.B2B_FP_Product_SKU_list_is_empty, 
                    B2B_FeaturedProducts_Util.ERROR), 
                    0, responseMap);

            return responseMap;
        }

        final String [] objFields = new String[]{'Id'
                                                    ,'Name'
                                                    ,'StockKeepingUnit'
                                                    ,'IsActive'
                                                };

        List<Product2> standardProductList = new List<Product2>();

        if(B2B_FeaturedProducts_SecurityUtils.checkIsAccessible('Product2', objFields)) {
            standardProductList = [Select Id, Name from Product2 where StockKeepingUnit in :skuList and IsActive = true limit :MAX_PRODUCTS];
        }

        // The following List is used only for test coverage purposes.
        List<String> productIdList = new List<String>();

        for(Product2 standardProduct : standardProductList) {

            String productId = standardProduct.Id;

            productIdList.add(productId);

        }

        featuredProductList = getProductDetails(productIdList, webstoreId, effectiveAccountId);

        //System.debug('featuredProductList: ' + JSON.serialize(featuredProductList));

        if(includePrices && featuredProductList.size() > 0) {
            getProductPriceDetails(featuredProductList, webstoreId, effectiveAccountId);
        }

        // System.debug('featuredProductList: ' + JSON.serialize(featuredProductList));

        data = JSON.serialize(featuredProductList);

        responseMap.put('data', data);

        return responseMap;

    }

    @AuraEnabled (cacheable=false)
    public static Map<String, Object> getProductsByCategoryId(String webstoreId, String effectiveAccountId, String categoryId, Boolean includePrices) {

        System.debug('inside getProductsBySku()');

        // System.debug('webstoreId: ' + webstoreId);
        // System.debug('effectiveAccountId: ' + effectiveAccountId);
        // System.debug('categoryId: ' + categoryId);
        // System.debug('includePrices: ' + includePrices);

        Map<String, Object> responseMap = new Map<String, Object>();
        
        String data = null;

        List<Object> featuredProductList = new List<Object>();

        List<B2B_FeaturedProducts_Util.ProductDetailWrapper> productList = new List<B2B_FeaturedProducts_Util.ProductDetailWrapper>();

        try {

            if(categoryId == null) {

                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(Label.B2B_FP_Component_configuration_error, Label.B2B_FP_CategoryId_is_blank, B2B_FeaturedProducts_Util.ERROR), 0, responseMap);

                throw new CustomException('Configuration Error');
            }

            final String [] objFields = new String[]{'Id'
                                                        ,'ProductId'
                                                        ,'ProductCategoryId'
                                                    };

            List<ProductCategoryProduct> categoryProductList = new List<ProductCategoryProduct>();

            if(B2B_FeaturedProducts_SecurityUtils.checkIsAccessible('ProductCategoryProduct', objFields)) {
                categoryProductList = [Select Id, ProductId from ProductCategoryProduct where ProductCategoryId = :categoryId limit :MAX_PRODUCTS];
            }

            // System.debug('categoryProductList.size() = ' + categoryProductList.size());

            if(categoryProductList.size() == 0) {

                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(Label.B2B_FP_Component_configuration_error, Label.B2B_FP_Category_contains_no_products, B2B_FeaturedProducts_Util.ERROR), 0, responseMap);

                throw new CustomException('Configuration Error');
            }

            // The following List is used only for test coverage purposes.
            List<String> productIdList = new List<String>();

            for(ProductCategoryProduct categoryProduct : categoryProductList) {

                String productId = categoryProduct.ProductId;

                productIdList.add(productId);

            }

            // System.debug('productIdList.size = ' + productIdList.size());

            // System.debug('productIdList: ' + productIdList);

            if(productIdList.size() == 0) {

                B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(Label.B2B_FP_Component_configuration_error, 'Category contains no products', B2B_FeaturedProducts_Util.ERROR), 0, responseMap);

                throw new CustomException('Configuration Error');
            }

            featuredProductList = getProductDetails(productIdList, webstoreId, effectiveAccountId);

            //System.debug('featuredProductList: ' + JSON.serialize(featuredProductList));

            if(includePrices && featuredProductList.size() > 0) {
                getProductPriceDetails(featuredProductList, webstoreId, effectiveAccountId);
            }

            // System.debug('featuredProductList: ' + JSON.serialize(featuredProductList));

        }
        catch (CustomException e) {}
        catch (Exception err) {
            B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message(Label.B2B_FP_Processing_Error, err.getMessage(), B2B_FeaturedProducts_Util.ERROR), 0, responseMap);
        }

        data = JSON.serialize(featuredProductList);

        responseMap.put('data', data);

        List<B2B_FeaturedProducts_Util.Message> retMessages = (List<B2B_FeaturedProducts_Util.Message>)responseMap.get('messages');

        String messagesJson = JSON.serialize(retMessages);
        // System.debug('messagesJson: ' + messagesJson);
        responseMap.put('messagesJson', messagesJson);

        return responseMap;

    }

    /*
        Utilzes the Connect Apex API to retrieve the product details for each product Id in the List.
    */
    private static List<Object> getProductDetails(List<String> productIdList, String webstoreId, String effectiveAccountId) {

        System.debug('getProductDetails() - begin');

        Boolean excludeFields = false;
        List<String> mediaGroups = new List<String>();
        Boolean excludeMedia = false;
        Boolean excludeEntitlementDetails = true;
        Boolean excludePrimaryProductCategory = true;

        List<String> fields = new List<String>();
        fields.add('StockKeepingUnit');
        fields.add('Name');
        fields.add('Description');

        List<B2B_FeaturedProducts_Util.ProductDetailWrapper> productList = new List<B2B_FeaturedProducts_Util.ProductDetailWrapper>();

        for(String productId : productIdList) {

            //System.debug('productId: ' + productId);

            ConnectApi.ProductDetail detail = null;

            if(Test.isRunningTest() == false) {
                // Call the Connect Apex API to get the product details from the catalog
                try {
                    detail = ConnectApi.CommerceCatalog.getProduct(webstoreId, productId, effectiveAccountId, fields, excludeFields, mediaGroups, excludeMedia, excludeEntitlementDetails, excludePrimaryProductCategory);
                }
                catch(ConnectApi.NotFoundException e) {
                    System.debug('Exception: ' + e.getMessage());
                    System.debug('Effective account is not entitled to this product: ' + productId);
                }
            }
            else {
                // Load the test data
                if(B2B_FeaturedProducts_ControllerTestUtils.productList == null) {
                    
                    B2B_FeaturedProducts_ControllerTestUtils.productList = B2B_FeaturedProducts_ControllerTestUtils.getProducts(productIdList);
                }

                detail = B2B_FeaturedProducts_ControllerTestUtils.getProductDetailTest(productId);
            }

            if(detail != null) {

                B2B_FeaturedProducts_Util.ProductDetailWrapper product = new B2B_FeaturedProducts_Util.ProductDetailWrapper();

                product.defaultImage = detail.defaultImage;

                // Need to convert the field data returned to match how the search REST API returns that data.
                Map<String, Object> fieldsMap = new Map<String, Object>();

                for(String fieldName : detail.fields.keySet()) {
                    String fieldValue = detail.fields.get(fieldName);

                    Map<String, String> fieldValueMap = new Map<String, String>{'value' => fieldValue};

                    fieldsMap.put(fieldName, fieldValueMap);

                }

                product.fields = fieldsMap;

                //product.fields = detail.fields;

                product.entitlement = detail.entitlement;
                product.mediaGroups = detail.mediaGroups;
                product.primaryProductCategoryPath = detail.primaryProductCategoryPath;
                product.id = detail.id;
                product.name = detail.fields.get('Name');

                productList.add(product);

            }

        }

        return productList;

    }

    /*
        Utilzes the Connect Apex API to retrieve the product pricing for each product Id in the List.
    */
    private static void getProductPriceDetails(List<Object> productList, String webstoreId, String effectiveAccountId) {

        System.debug('getProductPriceDetails() - begin');

        List<ConnectApi.PricingLineItemInput> pricingLineItems = new List<ConnectApi.PricingLineItemInput>();

        ConnectApi.PricingInput pricingInput = new ConnectApi.PricingInput();

        for(Object obj : productList) {

            B2B_FeaturedProducts_Util.ProductDetailWrapper product = (B2B_FeaturedProducts_Util.ProductDetailWrapper)obj;

            String productId = product.id;

            ConnectApi.PricingLineItemInput lineItem = new ConnectApi.PricingLineItemInput();
            lineItem.productId = productId;
    
            pricingLineItems.add(lineItem);

        }

        // System.debug('pricingLineItems size = ' + pricingLineItems.size());

        pricingInput.pricingLineItems = pricingLineItems;

        ConnectApi.PricingResult result = null;

        if(Test.isRunningTest() == false) {
            result = ConnectApi.CommerceStorePricing.getProductPrices(webstoreId, effectiveAccountId, pricingInput);
        }
        else {
            List<String> productIdList = new List<String>();

            for(ConnectApi.PricingLineItemInput lineItem : pricingLineItems) {
    
                String productId = lineItem.productId;
        
                productIdList.add(productId);
    
            }

            // Load the test data
            if(B2B_FeaturedProducts_ControllerTestUtils.pricebookEntryMap == null) {
                    
                B2B_FeaturedProducts_ControllerTestUtils.pricebookEntryMap = B2B_FeaturedProducts_ControllerTestUtils.getPricebookEntries(productIdList);
            }

            result = B2B_FeaturedProducts_ControllerTestUtils.getProductPricingTest(productIdList);
        }

        // System.debug('result: ' + JSON.serialize(result));

        List<ConnectApi.PricingResultLineItem> pricingLineItemResults = result.pricingLineItemResults;

        // Put all of the pricing results into a Map by productId
        Map<String, ConnectApi.PricingResultLineItem> pricingMap = new Map<String, ConnectApi.PricingResultLineItem>();

        for(ConnectApi.PricingResultLineItem resultLineItem : pricingLineItemResults) {

            String productId = resultLineItem.productId;

            pricingMap.put(productId, resultLineItem);

        }

        // System.debug('pricingMap: ' + JSON.serialize(pricingMap));

        for(Object obj : productList) {

            B2B_FeaturedProducts_Util.ProductDetailWrapper product = (B2B_FeaturedProducts_Util.ProductDetailWrapper)obj;

            String productId = product.id;

            if(productId.length() > 15) {
                productId = productId.substring(0, 15);
            }

            if(pricingMap.containsKey(productId)) {

                // System.debug('pricing found for product: ' + product.name);

                ConnectApi.PricingResultLineItem resultLineItem = pricingMap.get(productId);

                B2B_FeaturedProducts_Util.ProductPricingWrapper prices = new B2B_FeaturedProducts_Util.ProductPricingWrapper();

                prices.listPrice = resultLineItem.listPrice;
                prices.unitPrice = resultLineItem.unitPrice;
                prices.pricebookEntryId = resultLineItem.pricebookEntryId;

                product.prices = prices;

            }

        }

    }

    @AuraEnabled
    public static Map<String, String> fetchInitValues(String communityId, String effectiveAccountId) {

        Map<String, String> responseMap = new Map<String, String>();
        
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);

        responseMap.put('webstoreId', webstoreId);

        responseMap.put('effectiveAccountId', effectiveAccountId);

        return responseMap;

    }

    /*
        This method is used to convert the community Id to the web store Id.
    */

    @AuraEnabled
    public static String resolveCommunityIdToWebstoreId(String communityId) {
        if(communityId == null || communityId == '') {
            return null;
        }
        
        String webstoreId = null;

        List<WebStoreNetwork> wsnList = new List<WebStoreNetwork>();

        if(Schema.sObjectType.WebStoreNetwork.fields.WebStoreId.isAccessible()
        && Schema.sObjectType.WebStoreNetwork.fields.NetworkId.isAccessible()) {
            wsnList = [SELECT WebStoreId FROM WebStoreNetwork WHERE NetworkId = :communityId];
        }

        if(wsnList.size() > 0) {
            WebStoreNetwork wsn = wsnList.get(0);
            webstoreId = wsn.WebStoreId;
        }

        return webstoreId;
    }

    public class CustomException extends Exception {}

}