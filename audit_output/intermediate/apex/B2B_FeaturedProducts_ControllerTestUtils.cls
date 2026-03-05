@IsTest
public with sharing class B2B_FeaturedProducts_ControllerTestUtils {

    public static User createAdminUser() {

        System.debug('inside createAdminUser()');

        User u = new User();

        u.Username = 'testb2buser1@test.com';
        u.LastName = 'TestLastName';
        u.Email = 'testb2buser1@test.com';
        u.Alias = 'test1';
        u.TimeZoneSidKey = 'America/New_York';
        u.EmailEncodingKey = 'ISO-8859-1';
        u.ProfileId = [select id from Profile where Name = 'System Administrator'].Id;
        u.LanguageLocaleKey = 'en_US';
        u.LocaleSidKey = 'en_US';
        u.EmployeeNumber = '655321';

        // Do not assign a role to the user.  If you do, this can cause issues with the scratch org you are creating the package in.

        insert u;

        return u;
    }

    public static Id createUser(Id contactId) {

        System.debug('inside createUser()');

        User u = new User();

        u.Username = 'testb2buser2@test.com';
        u.LastName = 'TestLastName';
        u.Email = 'testb2buser2@test.com';
        u.Alias = 'test2';
        u.TimeZoneSidKey = 'America/New_York';
        u.EmailEncodingKey = 'ISO-8859-1';

        u.ProfileId = [select id from Profile where Name = 'Standard User'].Id;

        u.LanguageLocaleKey = 'en_US';
        u.LocaleSidKey = 'en_US';
        u.EmployeeNumber = '24601';
        u.ContactId = contactId;

        // Do not assign a role to the user.  If you do, this can cause issues with the scratch org you are creating the package in.

        insert u;

        return u.Id;
    }

    public static Id createAccount() {

        System.debug('inside createAccount()');

        Account account = new Account();

        account.Name = 'Ohana, LLC';
        account.Type = 'Customer';
        account.Phone = '1-313-555-1212';
        account.Website = 'https://detroit.org';

        insert account;

        return account.Id;
    }

    public static void assignPermissionSetToUser(Id userId, String permissionSetName) {

        System.debug('inside assignPermissionSetToUser()');

        PermissionSet perm = [Select Id, Name from PermissionSet where Name = :permissionSetName];

        PermissionSetAssignment psa = new PermissionSetAssignment (
            PermissionSetId = perm.Id, AssigneeId = userId
        );

        insert psa;
    }

    public static Id createPricebook() {

        Pricebook2 pb = new Pricebook2(
            IsActive = true
            , Description = 'Default price book'
            , Name = 'Standard Price Book'
        );

        insert pb;

        return pb.Id;
    }

    public static List<Product2> getProducts(List<String> productIdList) {
        List<Product2> productList = [Select Id, Name, Description, StockKeepingUnit from Product2 where Id in :productIdList];

        return productList;
    }

    public static Id createProduct2(String name, String sku, String description) {
        Product2 product = new Product2(
            IsActive = true
            , Name = name
            , StockKeepingUnit = sku
            , Description = description
            , ProductCode = sku
        );

        insert product;

        return product.Id;

    }

    public static Id createStandardPricebookEntry(Id productId) {

        Id pricebookId = Test.getStandardPricebookId();

        PricebookEntry pbe = new PricebookEntry(
            IsActive = true
            , UnitPrice = 1.98
            , Pricebook2Id = pricebookId
            , Product2Id = productId
            , UseStandardPrice = false
        );

        insert pbe;

        return pbe.Id;
    }

    public static Id createPricebookEntry(Id pricebookId, Id productId) {
        PricebookEntry pbe = new PricebookEntry(
            IsActive = true
            , UnitPrice = 1.98
            , Pricebook2Id = pricebookId
            , Product2Id = productId
        );

        insert pbe;

        return pbe.Id;
    }

    public static Id createWebStore(Id pricebookId) {

        WebStore store = new WebStore(
            DefaultLanguage = 'en_US'
            , Description = 'Test B2B LE Storefront'
            , MaxValuesPerFacet = 100
            , StrikethroughPricebookId = pricebookId
            , PricingStrategy = 'LowestPrice'
            , PaginationSize = 20
            , Name = 'Detroit Coffee'
            , SupportedLanguages = 'es;en_US'
            
        );

        insert store;
        
        return store.Id;

    }

    public static Id createProductCatalog() {
        ProductCatalog pc = new ProductCatalog(
            Name = 'Sample Catalog'
        );

        insert pc;

        return pc.Id;
    }

    public static Id createProductCategory(String catalogId, String categoryName) {

        ProductCategory pc = new ProductCategory(
            CatalogId = catalogId
            , Name = categoryName
            , IsNavigational = true
            , SortOrder = 1
        );

        insert pc;

        return pc.Id;

    }

    public static Id createProductCategoryProduct(String categoryId, String productId) {

        ProductCategoryProduct pcp = new ProductCategoryProduct(
            ProductCategoryId = categoryId
            , ProductId = productId
            , IsPrimaryCategory = true
        );

        insert pcp;

        return pcp.Id;

    }

    public static List<ProductCategoryProduct> getProductCategoryProducts(String categoryId) {

        List<ProductCategoryProduct> pcpList = new List<ProductCategoryProduct>();

        if(categoryId != null) {
            pcpList = [Select Id, ProductCategoryId, ProductId, IsPrimaryCategory from ProductCategoryProduct where ProductCategoryId = :categoryId];
        }

        return pcpList;

    }

    // This code is necessary in order to simulate calling the ConnectApi within code coverage.

    public static List<Product2> productList = null;

    public static ConnectApi.ProductDetail getProductDetailTest(String productId) {

        ConnectApi.ProductDetail pd = new ConnectApi.ProductDetail();

        Product2 productObj = null;

        for(Product2 product : productList) {
            if(product.Id == productId) {
                productObj = product;
                break;
            }
        }

        pd.id = productObj.Id;

        // Create the fields Map

        Map<String, String> fieldsMap = new Map<String, String>();

        fieldsMap.put('StockKeepingUnit', productObj.StockKeepingUnit);

        fieldsMap.put('Name', productObj.Name);

        fieldsMap.put('Description', productObj.Description);

        pd.fields = fieldsMap;

        // Create the product entitlement object
        ConnectApi.ProductEntitlement pe = new ConnectApi.ProductEntitlement();
        pe.canViewPrice = true;

        pd.entitlement = pe;

        // Create the product media

        ConnectApi.ProductMedia pm = new ConnectApi.ProductMedia();
        pm.id = '1';
        pm.alternateText = 'Coolest product image ever';
        pm.mediaType = ConnectApi.ProductMediaType.Image;
        pm.sortOrder = 1;
        pm.thumbnailUrl = null;
        pm.title = 'Some image';
        pm.url = '/image/path/picture.png';

        List<ConnectApi.ProductMedia> mediaItems = new List<ConnectApi.ProductMedia>();
        mediaItems.add(pm);

        ConnectApi.ProductMediaGroup pmg = new ConnectApi.ProductMediaGroup();
        pmg.developerName = 'productDetailImage';
        pmg.id = '1';
        pmg.mediaItems = mediaItems;

        List<ConnectApi.ProductMediaGroup> mediaGroups = new List<ConnectApi.ProductMediaGroup>();
        mediaGroups.add(pmg);

        return pd;

    }
    
    public static Map<String, List<PricebookEntry>> pricebookEntryMap = null;

    public static Map<String, List<PricebookEntry>> getPricebookEntries(List<String> productIdList) {

        pricebookEntryMap = new Map<String, List<PricebookEntry>>();

        List<PricebookEntry> allPricebookEntries = [Select Id, Name, UnitPrice, Pricebook2Id, Pricebook2.IsStandard, Product2Id, UseStandardPrice from PricebookEntry where Product2Id in :productIdList];

        for(PricebookEntry pbe : allPricebookEntries) {

            List<PricebookEntry> pricebookEntries = null;

            String productId = pbe.Product2Id;

            if(pricebookEntryMap.containsKey(productId)) {
                pricebookEntries = pricebookEntryMap.get(productId);
            }
            else {
                pricebookEntries = new List<PricebookEntry>();
            }

            pricebookEntries.add(pbe);

            pricebookEntryMap.put(productId, pricebookEntries);

        }

        return pricebookEntryMap;

    }

    public static ConnectApi.PricingResult getProductPricingTest(List<String> productIdList) {

        ConnectApi.PricingResult result = new ConnectApi.PricingResult();

        List<ConnectApi.PricingResultLineItem> pricingLineItemResults = new List<ConnectApi.PricingResultLineItem>();

        for(String productId : productIdList) {

            if(pricebookEntryMap.containsKey(productId)) {

                ConnectApi.PricingResultLineItem pricingResultLineItem = new ConnectApi.PricingResultLineItem();

                List<PricebookEntry> pricebookEntries = pricebookEntryMap.get(productId);

                for(PricebookEntry pbe : pricebookEntries) {
                    if(pbe.Pricebook2.IsStandard) {
                        pricingResultLineItem.ListPrice = String.valueOf(pbe.UnitPrice);
                    }
                    else {
                        pricingResultLineItem.UnitPrice = String.valueOf(pbe.UnitPrice);
                        pricingResultLineItem.pricebookEntryId = pbe.Id;
                    }

                    if(productId.length() > 15) {
                        pricingResultLineItem.productId = productId.substring(0, 15);
                    }
                    else {
                        pricingResultLineItem.productId = productId;
                    }

                }

                pricingResultLineItem.error = null;
                pricingResultLineItem.success = true;
                

                pricingLineItemResults.add(pricingResultLineItem);

            }

        }

        result.error = null;
        result.success = true;
        result.pricingLineItemResults = pricingLineItemResults;

        return result;

    }

}