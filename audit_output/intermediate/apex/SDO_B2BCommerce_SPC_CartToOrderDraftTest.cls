@IsTest
public with sharing class SDO_B2BCommerce_SPC_CartToOrderDraftTest {
    
    public static String effectiveAccountId = null;
    public static String shipToContactPointAddressId = null;
    public static Id cartId = null;
    public static String webstoreId = null;
    public static String deliveryMethodId = null;
    public static String cartDeliveryGroupId = null;
    public static String cartDeliveryGroupMethodId = null;
    public static Id pricebookId = null;
    
    private static void setup() {

        System.debug('begin setup()');

        Product2 product1 = new Product2(
            Name = 'TestProduct'
            , StockKeepingUnit = 'SKU_Test1'
            , Description = 'Test Product'
            , IsActive = true
        );

        insert product1;

        pricebookId = Test.getStandardPricebookId();

        PricebookEntry pbe = new PricebookEntry(
            IsActive = true
            , UnitPrice = 50
            , Pricebook2Id = pricebookId
            , Product2Id = product1.Id
            , UseStandardPrice = false
        );

        insert pbe;

        Account account = new Account(Name='TestAccount');
        insert account;
        effectiveAccountId = account.Id;

        WebStore webStore = new WebStore(Name='TestWebStore', SupportedLanguages='en_US', DefaultLanguage='en_US');
        insert webStore;
        webstoreId = webStore.Id;

        WebCart cart = new WebCart(
            Name='Cart'
            , WebStoreId=webStore.Id
            , AccountId=account.Id
            , PONumber = '24601'
            , Status = 'Active'
            , Type = 'Cart'
            , BillingStreet = '2100 Woodward Ave'
            
            , BillingCity = 'Detroit'
            , BillingState = 'MI'
            , BillingPostalCode = '48201'
            , BillingCountry = 'USA'
            );
        insert cart;
        cartId = cart.Id;

        System.debug('cartId: ' + cartId);

        CartDeliveryGroup cartDeliveryGroup = new CartDeliveryGroup(
            CartId=cart.Id
            , Name='Default Delivery'
            , DeliverToName ='Detroit IGHQ'
            , DeliverToState='MI'
            , DeliverToCountry='USA');
        insert cartDeliveryGroup;

        cartDeliveryGroupId = cartDeliveryGroup.Id;
        
        CartItem cartItem = new CartItem(
            CartId=cart.Id, 
            Sku='SKU_Test1', 
            Quantity=3.0, 
            Type='Product', 
            Name='TestProduct', 
            CartDeliveryGroupId=cartDeliveryGroup.Id
            , ListPrice = 50
            , SalesPrice = 50
            , TotalLineAmount = 150
            , TotalPrice = 150
            , Product2Id = product1.Id
        );
        insert cartItem;

        CartTax tax = new CartTax( 
                    Amount = 9,
                    CartItemId = cartItem.Id,
                    Name = 'GST',
                    TaxCalculationDate = Date.today(),
                    TaxRate = .06,
                    TaxType = 'Actual'
                );

        insert tax;

        List<ContactPointAddress> cpaList = new List<ContactPointAddress>();
        ContactPointAddress billingAddr = new ContactPointAddress(
            AddressType = 'Billing'
            , Street = '2100 Woodward Ave'
            , ParentId = effectiveAccountId
            , Name ='Detroit IGHQ'
            , City = 'Detroit'
            , State = 'MI'
            , PostalCode = '48201'
            , Country = 'USA'
            , IsDefault = true
            , IsPrimary = true
        );
        cpaList.add(billingAddr);

        ContactPointAddress shippingAddr = new ContactPointAddress(
            AddressType = 'Shipping'
            , Street = '2100 Woodward Ave'
            , ParentId = effectiveAccountId
            , Name ='Detroit IGHQ'
            , City = 'Detroit'
            , State = 'MI'
            , PostalCode = '48201'
            , Country = 'USA'
            , IsDefault = true
            , IsPrimary = true
        );
        cpaList.add(shippingAddr);

        insert(cpaList);

        shipToContactPointAddressId = cpaList.get(1).Id;

    }

    private static void setup2() {

        System.debug('begin setup2()');

        Product2 productA = new Product2(
            Name = 'Shipping Charge for this delivery method'
            , IsActive = true
        );

        insert productA;

        Id pricebookId = Test.getStandardPricebookId();

        PricebookEntry pbe = new PricebookEntry(
            IsActive = true
            , UnitPrice = 39.99
            , Pricebook2Id = pricebookId
            , Product2Id = productA.Id
            , UseStandardPrice = false
        );

        insert pbe;

        CartItem cartItem = new CartItem(
            CartId = cartId, 
            Quantity = 1.0
            , Type='Product'
            , Name='Shipping Cost'
            , CartDeliveryGroupId = cartDeliveryGroupId
            , ListPrice = 39.99
            , SalesPrice = 39.99
            , TotalLineAmount = 39.99
            , TotalPrice = 39.99
            , Product2Id = productA.Id
        );
        insert cartItem;

        CartTax tax = new CartTax( 
                    Amount = 2.40,
                    CartItemId = cartItem.Id,
                    Name = 'GST',
                    TaxCalculationDate = Date.today(),
                    TaxRate = .06,
                    TaxType = 'Actual'
                );

        insert tax;

        OrderDeliveryMethod defaultOrderDeliveryMethod = new OrderDeliveryMethod(
                    Name = 'Order Delivery Method1',
                    Carrier = 'DHL',
                    isActive = true,
                    ProductId = productA.Id,
                    ClassOfService = 'DHLND9'
                );
        insert(defaultOrderDeliveryMethod);

        deliveryMethodId = defaultOrderDeliveryMethod.Id;

        String shippingOptionProvider = 'DHLND9';
        String shippingOptionName = 'Next day 9am';
        Decimal shippingOptionRate = 39.99;


        CartDeliveryGroupMethod cartDeliveryGroupMethod = new CartDeliveryGroupMethod(
            CartDeliveryGroupId = cartDeliveryGroupId,
            DeliveryMethodId = deliveryMethodId,
            ExternalProvider = shippingOptionProvider,
            Name = shippingOptionName,
            ShippingFee = shippingOptionRate,
            WebCartId = cartId
        );
        insert(cartDeliveryGroupMethod);

        cartDeliveryGroupMethodId = cartDeliveryGroupMethod.Id;

        CartDeliveryGroup cartDeliveryGroup = [SELECT Id, DeliveryMethodId FROM CartDeliveryGroup WHERE Id= :cartDeliveryGroupId][0];
        cartDeliveryGroup.DeliveryMethodId = deliveryMethodId;
        update cartDeliveryGroup;

    }

    /*
        Test getting the cart summary, where a delivery method has been selected.
    */
    @isTest static void testCode1() {

        setup();

        // Additional setup to associate a cart delivery group method with the cart delivery group.
        setup2();
        
        SDO_B2BCommerce_SPC_CartToOrderDraft.Request request = new SDO_B2BCommerce_SPC_CartToOrderDraft.Request();
        request.cartId = cartId;
        request.pricebookId = pricebookId;

        List<SDO_B2BCommerce_SPC_CartToOrderDraft.Request> requestList = new List<SDO_B2BCommerce_SPC_CartToOrderDraft.Request>();
        requestList.add(request);

        Test.startTest();

        List<ID> orderIds = SDO_B2BCommerce_SPC_CartToOrderDraft.cartToOrder(requestList);      
        
        Test.stopTest();
    }

}